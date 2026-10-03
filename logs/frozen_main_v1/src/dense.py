"""Pinned MiniLM encoder with local per-text checkpoints. No remote inference."""
from pathlib import Path
import hashlib,json,os
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

ROOT=Path(__file__).resolve().parents[1]
class DenseEncoder:
    def __init__(self):
        self.model_dir=ROOT/"data/models/minilm"
        metadata=json.loads((self.model_dir/"model_metadata.json").read_text())
        self.revision=metadata["sha"]
        self.encoder_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        self.cache=ROOT/"outputs/embedding_cache"/(self.revision+"-"+self.encoder_hash[:12])
        self.cache.mkdir(parents=True,exist_ok=True)
        self.tokenizer=Tokenizer.from_file(str(self.model_dir/"tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=256)
        self.tokenizer.enable_padding(pad_id=0,pad_token="[PAD]")
        options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
        self.session=ort.InferenceSession(str(self.model_dir/"onnx/model.onnx"),options,providers=["CPUExecutionProvider"])
        self.input_names={x.name for x in self.session.get_inputs()}
    def key(self,text):return hashlib.sha256(text.encode()).hexdigest()
    def raw_encode(self,texts):
        enc=self.tokenizer.encode_batch(texts)
        inputs={"input_ids":np.asarray([e.ids for e in enc],dtype=np.int64),
                "attention_mask":np.asarray([e.attention_mask for e in enc],dtype=np.int64),
                "token_type_ids":np.asarray([e.type_ids for e in enc],dtype=np.int64)}
        hidden=self.session.run(None,{k:v for k,v in inputs.items() if k in self.input_names})[0]
        mask=inputs["attention_mask"][...,None]
        vectors=(hidden*mask).sum(axis=1)/np.maximum(mask.sum(axis=1),1)
        vectors=vectors/np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-12)
        info=[{"truncated":bool(e.overflowing),"visible_wordpieces":int(sum(e.attention_mask))-2} for e in enc]
        return vectors.astype(np.float32),info
    def cached(self,text):
        p=self.cache/(self.key(text)+".npy");m=p.with_suffix(".json")
        if not p.exists() or not m.exists():return False
        try:
            info=json.loads(m.read_text());v=np.load(p,allow_pickle=False)
            return (info["revision"]==self.revision and info["encoder_hash"]==self.encoder_hash
                    and info["text_sha256"]==self.key(text) and v.shape==(384,)
                    and bool(np.isfinite(v).all()))
        except (ValueError,KeyError,OSError):return False
    def encode(self,texts):
        unique=list(dict.fromkeys(texts))
        missing=[t for t in unique if not self.cached(t)]
        for start in range(0,len(missing),16):
            batch=missing[start:start+16];vectors,info=self.raw_encode(batch)
            for t,v,m in zip(batch,vectors,info):
                p=self.cache/(self.key(t)+".npy");tmp=p.with_suffix(".tmp")
                with tmp.open("wb") as f:np.save(f,v)
                tmp.replace(p)
                meta=p.with_suffix(".json");mt=meta.with_suffix(".json.tmp")
                mt.write_text(json.dumps({"revision":self.revision,"encoder_hash":self.encoder_hash,"text_sha256":self.key(t),**m})+"\n")
                mt.replace(meta)
        return np.stack([np.load(self.cache/(self.key(t)+".npy"),allow_pickle=False) for t in texts])
    def info(self,text):return json.loads((self.cache/(self.key(text)+".json")).read_text())
_ENCODER=None
def get_encoder():
    global _ENCODER
    if _ENCODER is None:_ENCODER=DenseEncoder()
    return _ENCODER
def dense_scores(query,units):
    e=get_encoder();vectors=e.encode([query]+units)
    return (vectors[1:]@vectors[0]).astype(float).tolist()

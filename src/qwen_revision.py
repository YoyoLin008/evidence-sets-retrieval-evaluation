"""Result-blind CPU timing gate and, only if passed, complete cached inference."""
from pathlib import Path
import json, hashlib, time, datetime, platform, subprocess, os
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'revisions/v2/compute'
INSTRUCTION='Given a scientific question or claim, retrieve passages that provide evidence relevant to it'
REVISION='97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3'
def sha(x): return hashlib.sha256(x).hexdigest()
def query_text(s): return f'Instruct: {INSTRUCTION}\nQuery:{s}'
def last_token_pool(hidden, mask):
    if bool((mask[:,-1].sum()==mask.shape[0]).item()): return hidden[:,-1]
    return hidden[torch.arange(hidden.shape[0]),mask.sum(1)-1]
def main():
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    torch.manual_seed(20261002);torch.use_deterministic_algorithms(True)
    config=dict(model='Qwen/Qwen3-Embedding-0.6B',revision=REVISION,dtype='float32',device='cpu',batch_size=1,threads=2,interop_threads=1,max_length=8192,pooling='last_nonpadding_token',dimensions=1024,normalize=True,instruction=INSTRUCTION,seed=20261002,attention='sdpa',gate_seconds=7200)
    freeze=OUT/'runtime_freeze.json'
    config['source_sha256']=sha(Path(__file__).read_bytes())
    if freeze.exists(): assert json.loads(freeze.read_text())['config']==config
    else: freeze.write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),config=config,platform=platform.platform(),processor=platform.processor()),indent=2))
    from importlib.metadata import distributions
    (OUT/'requirements.lock.txt').write_text('\n'.join(sorted(d.metadata['Name']+'=='+d.version for d in distributions()))+'\n')
    files={str(p.relative_to(OUT/'model')):sha(p.read_bytes()) for p in (OUT/'model').rglob('*') if p.is_file() and '.cache' not in p.parts}
    (OUT/'model_manifest.json').write_text(json.dumps(files,indent=2))
    xs=[json.loads(s) for s in (ROOT/'outputs/main_v1/instances.jsonl').read_text().splitlines()]
    texts={sha(t.encode()):t for x in xs for t in x['units']+[query_text(x['query'])]}
    tok=AutoTokenizer.from_pretrained(OUT/'model',local_files_only=True,padding_side='left')
    lengths={h:len(tok(t,truncation=False)['input_ids']) for h,t in texts.items()}
    ordered=sorted(texts,key=lambda h:(lengths[h],h))
    bins=[list(z) for z in np.array_split(ordered,4)]
    sample=[]
    for b,hs in enumerate(bins):
        chosen=sorted(hs)[:32]
        longest=max(hs,key=lambda h:(lengths[h],h))
        if longest not in chosen: chosen.append(longest)
        sample.extend(dict(bin=b,hash=h,length=lengths[h]) for h in chosen)
    (OUT/'timing_sample.json').write_text(json.dumps(dict(selection='SHA256 first 32 per equal-count length quartile plus longest per bin',bin_counts=[len(x) for x in bins],texts=len(texts),truncated=sum(v>8192 for v in lengths.values()),lengths=lengths,sample=sample),indent=2))
    print('Loading pinned model; timing',len(sample),'of',len(texts),'unique inputs',flush=True)
    start=time.perf_counter()
    model=AutoModel.from_pretrained(OUT/'model',local_files_only=True,torch_dtype=torch.float32,attn_implementation='sdpa').to('cpu').eval()
    load_seconds=time.perf_counter()-start
    cache=OUT/'embeddings';cache.mkdir(exist_ok=True)
    def encode(h):
        batch=tok([texts[h]],padding=True,truncation=True,max_length=8192,return_tensors='pt')
        with torch.inference_mode():
            out=model(**batch,use_cache=False)
            emb=torch.nn.functional.normalize(last_token_pool(out.last_hidden_state,batch['attention_mask']),p=2,dim=1)
        arr=emb.cpu().numpy().astype(np.float32)
        assert arr.shape==(1,1024) and np.isfinite(arr).all() and abs(np.linalg.norm(arr)-1)<1e-5
        return arr[0]
    # Deterministic warm-up: shortest input. Its duration is recorded but excluded from bin averages.
    start=time.perf_counter();encode(ordered[0]);warmup=time.perf_counter()-start
    for j,r in enumerate(sample):
        start=time.perf_counter();arr=encode(r['hash']);r['seconds']=time.perf_counter()-start
        np.save(cache/(r['hash']+'.npy'),arr)
        with (OUT/'timing_rows.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
        if (j+1)%16==0:print('Timed',j+1,'/',len(sample),flush=True)
    means=[np.mean([r['seconds'] for r in sample if r['bin']==b]) for b in range(4)]
    projected=float(sum(len(hs)*means[b] for b,hs in enumerate(bins))+load_seconds+warmup)
    gate=dict(projected_seconds=projected,threshold_seconds=7200,bin_mean_seconds=means,bin_counts=[len(x) for x in bins],load_seconds=load_seconds,warmup_seconds=warmup,passed=projected<=7200,effectiveness_computed=False,sample_n=len(sample),unique_inputs=len(texts),note='Length-bin sample includes longest; projection is an estimate, not a confidence bound.')
    (OUT/'feasibility.json').write_text(json.dumps(gate,indent=2))
    print(json.dumps(gate),flush=True)
    if not gate['passed']: return
    fullstart=time.perf_counter()
    for j,h in enumerate(sorted(texts)):
        p=cache/(h+'.npy')
        if not p.exists():np.save(p,encode(h))
        if (j+1)%500==0:print('Encoded',j+1,'/',len(texts),'elapsed',round(time.perf_counter()-fullstart),flush=True)
    (OUT/'inference_complete.json').write_text(json.dumps(dict(unique_inputs=len(texts),full_additional_seconds=time.perf_counter()-fullstart,cache_manifest={p.name:sha(p.read_bytes()) for p in cache.glob('*.npy')},config=config),indent=2))
if __name__=='__main__':main()

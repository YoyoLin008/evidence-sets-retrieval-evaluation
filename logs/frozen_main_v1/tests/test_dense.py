import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from dense import get_encoder

def test_dense_dimension_norm_and_repeat():
    e=get_encoder()
    x=e.encode(["A cat sits on a mat.","A cat sits on a mat.","Neutrinos are elementary particles."])
    assert x.shape==(3,384) and np.isfinite(x).all()
    np.testing.assert_allclose(np.linalg.norm(x,axis=1),1,atol=1e-6)
    np.testing.assert_array_equal(x[0],x[1])
    assert (x[0]@x[1])>(x[0]@x[2])

def test_padding_invariance_and_truncation():
    e=get_encoder()
    x,_=e.raw_encode(["Short text."])
    y,info=e.raw_encode(["Short text.","Longer text with more words."])
    np.testing.assert_allclose(x[0],y[0],atol=2e-6)
    _,info=e.raw_encode(["word "*500])
    assert info[0]["truncated"] and info[0]["visible_wordpieces"]==254

def test_incomplete_cache_recovers(tmp_path):
    from dense import DenseEncoder
    e=DenseEncoder();e.cache=tmp_path
    text="Cache recovery test."
    a=e.encode([text])
    (tmp_path/(e.key(text)+".json")).unlink()
    assert not e.cached(text)
    b=e.encode([text])
    assert e.cached(text) and np.allclose(a,b)

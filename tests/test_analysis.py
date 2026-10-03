import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from analyze import bootstrap_matrix,estimate

def test_cluster_means_are_item_weighted():
    values=np.array([1.,1.,0.]);boot=(np.array([0,0,1]),np.array([2,1]),np.array([[1,1],[2,0],[0,2]]))
    mean,ci=estimate(values,boot)
    assert mean[0]==2/3
    np.testing.assert_allclose(ci[0],np.quantile([2/3,1.,0.],[.025,.975]))

def test_paired_bootstrap_linear_difference():
    b=bootstrap_matrix(["a","a","b","c"],b=500)
    x=np.array([1,0,1,0.]);y=np.array([0,1,0,0.])
    m,ci=estimate(x-y,b)
    assert m[0]==(x.mean()-y.mean()) and ci.shape==(1,2)
    assert np.all(estimate(np.zeros(4),b)[1]==0)

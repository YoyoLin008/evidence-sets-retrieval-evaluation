"""Run in the pinned revision environment; no model load or effectiveness scoring."""
import torch,json
from pathlib import Path
from qwen_revision import last_token_pool
h=torch.arange(24,dtype=torch.float32).reshape(2,4,3)
for mask,expected in [(torch.tensor([[0,0,1,1],[0,1,1,1]]),h[:,-1]),(torch.tensor([[1,1,0,0],[1,1,1,0]]),torch.stack([h[0,1],h[1,2]])),(torch.ones((2,4),dtype=torch.long),h[:,-1])]:
 p=last_token_pool(h,mask);assert torch.equal(p,expected)
 assert torch.allclose(torch.nn.functional.normalize(p,p=2,dim=1).norm(dim=1),torch.ones(2))
print(json.dumps({'passed':True,'cases':['left padding','right padding','un-padded','normalization'],'scope':'pooling only; no effectiveness scoring'}))

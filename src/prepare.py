"""Acquire exact documented inputs and safely extract public benchmark archives."""
import argparse,json,hashlib,tarfile
from pathlib import Path
from acquire import acquire,ROOT
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--literature",action="store_true");a=parser.parse_args()
    expected=json.loads((ROOT/"configs/acquisition_expected.json").read_text())
    required={p:v for p,v in expected.items() if a.literature or p.startswith("data/") or p in [
      "literature/sources/scifact_evaluator.py.txt","literature/sources/irrj_template.zip"]}
    # Do not let a newly moved 'latest' URL silently replace the frozen data.
    needed={p:v["url"] for p,v in required.items() if not (ROOT/p).exists()}
    acquire(needed)
    for p,v in required.items():
        path=ROOT/p
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=v["sha256"]:
            raise ValueError(f"Source unavailable or changed: {p}. Obtain the exact archived bytes; do not silently update the study.")
    targets={"data/raw/scifact.tar.gz":"data/raw/scifact",
             "data/raw/qasper-train-dev-v0.3.tgz":"data/raw/qasper-train-dev-v0",
             "data/raw/qasper-test-and-evaluator-v0.3.tgz":"data/raw/qasper-test-and-evaluator-v0"}
    for src,dest in targets.items():
        directory=ROOT/dest;directory.mkdir(parents=True,exist_ok=True)
        with tarfile.open(ROOT/src) as archive:archive.extractall(directory,filter="data")
    print("Verified and extracted fixed public inputs.")
if __name__=="__main__":main()

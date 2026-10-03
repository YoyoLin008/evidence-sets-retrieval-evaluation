"""Compare fresh rankings with supplied reference outputs; ignore run timestamps."""
from pathlib import Path
import argparse,json,math
ROOT=Path(__file__).resolve().parents[1]
def read(path):
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    keyed={(r["dataset"],r["id"],r["method"]):r for r in rows}
    assert len(keyed)==len(rows),"Duplicate item/method records"
    return keyed
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reference",type=Path,default=ROOT/"reference_outputs/main_v1/rankings.jsonl")
    a=p.parse_args()
    expected=read(a.reference);observed=read(ROOT/"outputs/main_v1/rankings.jsonl")
    assert expected.keys()==observed.keys(),"Item/method set differs"
    maxdelta=0.
    for key,x in expected.items():
        y=observed[key]
        for field in ["ranking","gold","points","costs","topology","cluster","unit_count"]:
            assert x[field]==y[field],(key,field)
        assert len(x["retrieval_scores"])==len(y["retrieval_scores"])
        for xs,ys in zip(x["retrieval_scores"],y["retrieval_scores"]):
            assert math.isfinite(xs) and math.isfinite(ys)
            maxdelta=max(maxdelta,abs(xs-ys))
    print(json.dumps({"records":len(observed),"rankings_and_outcomes_identical":True,"maximum_score_difference":maxdelta},indent=2))
if __name__=="__main__":main()

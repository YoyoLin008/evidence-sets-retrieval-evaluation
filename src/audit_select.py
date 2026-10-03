"""Record screening and deterministic selection before representation classification."""
from pathlib import Path
import json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1]/'revisions/v2/audit'
def main():
 data=json.loads((ROOT/'candidate_metadata.json').read_text())
 q=[46,47,49,52,59,89,90,91,92,93,94,95,96,97,98,99,102,105,106,110,112,116,117,119,121,123]
 s=[21,39,42,63,64,65,67,72,75,79,80,81,82,83,85,125,126,127,128,129,130,131,133,134,135,138,139,140,141,142,143,145,146]
 mirrors={45:(39,'same NanoBEIR statement-to-question distribution family; language variant'),101:(96,'SARA release linked from SARA implementation'),103:(99,'byte-identical qasper.py loader'),111:(99,'byte-identical qasper.py loader'),115:(99,'byte-identical qasper.py loader'),122:(121,'vendored MemoRAG subtree with upstream README'),87:(80,'same named project and linked GitHub distribution'),132:(126,'BEIR SciFact distribution linked to BEIR implementation'),144:(126,'BEIR qrels companion distribution'),147:(126,'BEIR dataset copy; no separate converter documented'),137:(129,'Hugging Face SciFact loader derivative; same source dataset schema; code differences retained for lineage check')}
 refs={107:'QASPER',124:'SciFact',136:'SciFact'}
 excludes={104:'benchmark description only; no loader/converter/evaluator in discovered page',108:'leaderboard only',109:'copy of official evaluator, no separate pipeline exposed',118:'MultiCite data converted to QASPER schema; not QASPER benchmark annotations',120:'unrelated QasperAI product',84:'curated links only',48:'curated benchmark links only',86:'GitHub topic navigation',100:'inaccessible HF dataset (401); eligibility unverified',113:'inaccessible HF dataset (401); eligibility unverified',114:'inaccessible HF dataset (401); eligibility unverified'}
 eligible={i:'QASPER' for i in q}|{i:'SciFact' for i in s};screen=[];families=[]
 for i,r in enumerate(data):
  if i in refs:status='official_reference';reason='original benchmark implementation/evaluator';family='github.com/allenai/scifact' if refs[i]=='SciFact' else r['canonical']
  elif i in mirrors:status='lineage_duplicate';j,reason=mirrors[i];family=data[j]['canonical']
  elif i in eligible:status='eligible';reason='public benchmark-specific loader, distribution, conversion, or evaluation pipeline evidenced by README or discovered file';family=r['canonical']
  else:status='excluded';reason=excludes.get(i,'screened result describes another dataset/task or is a mention-only result; no target benchmark pipeline established from discovered artifact');family=None
  rec=dict(index=i,canonical=r['canonical'],status=status,reason=reason,family=family,benchmark=eligible.get(i,refs.get(i)),queries=r['queries'],screening_source=r['directory']+'/README.source',inaccessible=bool(r.get('readme_error')))
  screen.append(rec)
  if status=='eligible':families.append(dict(**rec,selection_hash=hashlib.sha256(family.lower().encode()).hexdigest()))
 for b in ['QASPER','SciFact']:
  fs=sorted([r for r in families if r['benchmark']==b],key=lambda r:r['selection_hash'])
  for rank,r in enumerate(fs,1):r.update(selection_rank=rank,selected=rank<=15)
 (ROOT/'screening.json').write_text(json.dumps(screen,indent=2));(ROOT/'selected_families.json').write_text(json.dumps(families,indent=2))
 manifest={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'eligibility_counts':{b:sum(r['benchmark']==b for r in families) for b in ['QASPER','SciFact']},'selected_per_benchmark':15,'selection_sha256':hashlib.sha256((ROOT/'selected_families.json').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'note':'Selection frozen before representation classification. Mirrors of selected projects inspected as provenance, not independent counts. Unknown lineage relationships will be disclosed if later evidence changes deduplication.'}
 (ROOT/'selection_freeze.json').write_text(json.dumps(manifest,indent=2))
 for r in sorted(families,key=lambda r:(r['benchmark'],r['selection_rank'])):
  if r['selected']:print(r['index'],r['benchmark'],r['canonical'])
if __name__=='__main__':main()

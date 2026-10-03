from pathlib import Path
import json,urllib.request,hashlib,concurrent.futures
ROOT=Path(__file__).resolve().parents[1]/'revisions/v2/audit'
PATHS={
49:['benchmark/RAG/src/adapters/qasper_adapter.py','benchmark/RAG/dataset_tools/converters.py','benchmark/RAG/src/core/metrics.py'],
65:['src/data/dataset_loader.py','src/evaluation/retrieval_metrics.py','scripts/evaluation/evaluate.py'],
75:['docs/reproduce/from-document-collection/beir-v1.0.0-scifact.flat.md','src/main/resources/reproduce/from-document-collection/configs/beir-v1.0.0-scifact.flat.yaml'],
80:['src/jev_rag_bench/data.py','src/jev_rag_bench/metrics.py'],81:['src/jev_rag_benchmark/data.py','src/jev_rag_benchmark/metrics.py'],
82:['benchmarking/rag/benchmarks/beir_bench.py','benchmarking/rag/lib/metrics.py'],83:['src/data_loader.py','src/metrics.py'],
90:['evaluator/dataset_evaluator.py','baselines/src/metrics/metrics.py','baselines/src/utils/duplicates.py'],
91:['create_qasper_examples_scibert.py','dataset.py','convert_retreived_evidence_to_dataset.py','qasper-led-baseline/scripts/evaluator.py'],
92:['src/lighteval/tasks/tasks/qasper.py'],97:['dataset_utils.py'],98:['LongBench-rwkv/eval.py','LongBench-rwkv/pred.py','LongBench-rwkv/metrics.py'],
105:['scripts/benchmarks/prepare_qasper.py','chunklab/eval/metrics.py'],110:['rank_bench.py'],
116:['src/convert_qasper.py','scripts/run_qasper_e2e.sh','data/qasper/qasper_evaluator.py'],
117:['scripts/experiments/qasper_to_gold_file.py','acl_verbatim/eval/evaluate_predictions.py','acl_verbatim/eval/span_metrics.py'],
119:['evaluate.py'],123:['src/sage/eval/benchmarks.py','src/sage/eval/dataset.py','src/sage/eval/metrics.py','src/sage/eval/span_mapping.py'],
127:['script/run_eval.py'],128:['download_data.py','evaluation.py'],
107:['qasper_baselines/dataset_reader.py','scripts/evaluator.py'],124:['verisci/evaluate/lib/data.py','verisci/evaluate/lib/metrics.py','doc/evaluation.md'],136:['evaluator/eval.py'],
42:['qrels_test.parquet','README.md'],59:['qasper-dataset/train-00000-of-00001.parquet','README.md'],79:['test.tsv','README.md'],
99:['qasper.py'],112:['QASPER-qrels/test-00000-of-00001.parquet','QASPER-queries/test-00000-of-00001.parquet','README.md'],
129:['scifact.py'],130:['scifact.py'],138:['data/test-00000-of-00001.parquet','README.md'],143:['qrels/test-00000-of-00001.parquet','provenance.json','README.md'],146:['README.md']}
def main():
 pins={r['index']:r for r in json.loads((ROOT/'pins.json').read_text())};jobs=[]
 for i,paths in PATHS.items():
  r=pins[i]
  for path in paths:jobs.append((r,path))
 def job(task):
  r,path=task;base=ROOT/r['directory']/'files';target=base/path;target.parent.mkdir(parents=True,exist_ok=True)
  host=r['canonical'];rev=r['revision']
  url=('https://raw.githubusercontent.com/'+host[11:]+'/'+rev+'/'+path) if host.startswith('github.com/') else ('https://huggingface.co/datasets/'+host[15:]+'/resolve/'+rev+'/'+path)
  rec=dict(index=r['index'],path=path,url=url,revision=rev,local=str(target.relative_to(ROOT)))
  try:
   data=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'EvidenceRepresentationResearch/2.0'}),timeout=90).read();target.write_bytes(data);rec.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
  except Exception as e:rec['error']=str(e)
  return rec
 with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:out=list(pool.map(job,jobs))
 (ROOT/'file_manifest.json').write_text(json.dumps(out,indent=2));print('files',len(out),'errors',[x for x in out if x.get('error')])
if __name__=='__main__':main()

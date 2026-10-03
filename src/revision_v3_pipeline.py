"""Revision-added exploratory SSCC conversion and real scorer replay.

No downstream retriever/generator is rerun. The original paper-local rankings are
passed to the pinned downstream scorer after explicit candidate/ID alignment.
Third-party source is fetched by commit into an ignored cache, never vendored.
"""
from __future__ import annotations
import argparse, ast, collections, csv, dataclasses, datetime, hashlib, importlib.metadata
import importlib.util, json, math, platform, shutil, sys, types, urllib.request
from pathlib import Path
import numpy as np
from evidence import ROOT, qasper_instances, load_jsonl, normalized, score, topology
from analyze import bootstrap_matrix, estimate

REVISION = 'da7e8fb13f297969d344bad90295b15c2917a47d'
UPSTREAM = 'qarkapp/sscc-rag-paper'
FILES = {
 'src/sage/eval/benchmarks.py':'a63f3d5d5fbaaa6636717ec5a8887f3c265cb857403b7f4b65d9afa1c5a276c6',
 'src/sage/eval/dataset.py':'4c9026b49e8989da74ccbd250ef47e67d087c34391030d6fcf366b09644a3f11',
 'src/sage/eval/metrics.py':'e344792d6f57ea0613f587ccd2a2370bfc3f09c9a71950df9dbf47c1e234cc72',
}
METHODS = ['bm25','tfidf','dense','lead','random']
MEASURES = ['nDCG@10','R@5','R@10','Success@5','Success@10','RR@10']

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, data):
 path.parent.mkdir(parents=True, exist_ok=True)
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
def write_csv(path, rows):
 with path.open('w') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def digest_data(data): return hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def acquire(cache):
 for relative, expected in FILES.items():
  path=cache/relative
  if not path.exists():
   path.parent.mkdir(parents=True,exist_ok=True)
   path.write_bytes(urllib.request.urlopen(f'https://raw.githubusercontent.com/{UPSTREAM}/{REVISION}/{relative}',timeout=120).read())
  if sha(path)!=expected: raise ValueError(f'Pinned upstream hash mismatch: {relative}')
 return cache

def load_upstream(cache):
 """Execute pinned functions unchanged; omit two unused indexing type imports.

 The dataset module otherwise executes unchanged AST. The imports refer only to
 unrelated index-building routines, which this conversion/scoring replay does
 not invoke. Dataclasses, converter, data-file loader and metrics are upstream.
 """
 for name in ['sage','sage.eval']:
  if name not in sys.modules:
   m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
 for leaf in ['dataset','benchmarks','metrics']:
  path=cache/f'src/sage/eval/{leaf}.py';name=f'sage.eval.{leaf}'
  tree=ast.parse(path.read_text(),filename=str(path))
  if leaf=='dataset':
   tree.body=[n for n in tree.body if not (isinstance(n,ast.ImportFrom) and n.module in ['sage.core.protocols','sage.core.types'])]
  module=types.ModuleType(name);module.__file__=str(path);sys.modules[name]=module
  exec(compile(tree,str(path),'exec'),module.__dict__)
 return sys.modules['sage.eval.dataset'],sys.modules['sage.eval.benchmarks'],sys.modules['sage.eval.metrics']

def convert_supplied(loader, papers):
 original=loader._qasper_json
 try:
  loader._qasper_json=lambda cache_dir,split:papers
  return loader.load_qasper(split='validation',max_papers=None)
 finally: loader._qasper_json=original

def normalized_alignment(instance, corpus):
 """Map each unique source body unit to first exported exact-normalized text.

 The export includes abstract and duplicate raw body paragraphs. Multiple export
 IDs with the same normalized text are retained in the audit; never silently
 assert exact membership when the converter picked a different ID.
 """
 bytext=collections.defaultdict(list)
 for pid,text in corpus.items():
  if pid.split('::',1)[0]==instance.cluster: bytext[normalized(text)].append(pid)
 mapping={i:bytext[body][0] for i,body in enumerate(instance.units) if body in bytext}
 ambiguity={i:bytext[body] for i,body in enumerate(instance.units) if len(bytext[body])>1}
 return mapping,ambiguity

def membership_category(source_ids,export_ids,complete_mapping=True):
 if not complete_mapping:return 'undetermined_source_correspondence'
 if set(source_ids)==set(export_ids):return 'exact_union_membership'
 if set(export_ids)<set(source_ids):return 'missing_or_filtered_membership'
 if set(source_ids)<set(export_ids):return 'additional_membership'
 return 'changed_membership'

def conventional(order, relevant, k):
 relevant=set(relevant);prefix=order[:k];hits=[int(x in relevant) for x in prefix]
 dcg=sum(x/math.log2(i+2) for i,x in enumerate(hits))
 ideal=sum(1/math.log2(i+2) for i in range(min(k,len(relevant))))
 return {'recall':sum(hits)/len(relevant),'success':int(any(hits)),
         'ndcg':dcg/ideal if ideal else 0.,'rr':next((1/(i+1) for i,h in enumerate(hits) if h),0.)}

def summarize_saved(out):
 """Rebuild statistics from public per-query results without data or models."""
 provenance=json.loads((out/'manifest.json').read_text())
 if sha(out/'per_query_scores.csv')!=provenance['outputs_sha256']['per_query_scores.csv']:raise ValueError('Saved per-query results differ from execution manifest')
 with (out/'per_query_scores.csv').open() as f:rows=list(csv.DictReader(f))
 metrics=[k for k in rows[0] if k not in ['id','paper_id','method','k']]
 by_method={m:[r for r in rows if r['method']==m] for m in METHODS}
 ids=[r['id'] for r in by_method[METHODS[0]]]
 if len(ids)!=len(set(ids)):raise ValueError('Duplicate saved query IDs')
 clusters=[r['paper_id'] for r in by_method[METHODS[0]]];boot=bootstrap_matrix(clusters);summary=[]
 for method,rs in by_method.items():
  if [r['id'] for r in rs]!=ids or [r['paper_id'] for r in rs]!=clusters:raise ValueError('Unpaired saved scorer rows')
  for metric in metrics:
   mean,ci=estimate([float(r[metric]) for r in rs],boot)
   summary.append({'method':method,'n':len(rs),'clusters':len(set(clusters)),'metric':metric,'mean':float(mean[0]),'lo':float(ci[0,0]),'hi':float(ci[0,1]),'status':'revision-added exploratory'})
 write_csv(out/'score_summary.csv',summary)
 contrasts=[]
 for metric in ['R@5','Success@5','nDCG@10','RR@10','complete','union_complete','max_f1','union_f1']:
  values=[float(a[metric])-float(b[metric]) for a,b in zip(by_method['dense'],by_method['bm25'])]
  mean,ci=estimate(values,boot)
  contrasts.append({'contrast':'MiniLM minus BM25','metric':metric,'n':len(values),'mean':float(mean[0]),'lo':float(ci[0,0]),'hi':float(ci[0,1]),'status':'revision-added exploratory'})
 write_csv(out/'paired_contrasts.csv',contrasts)
 for name in ['score_summary.csv','paired_contrasts.csv']:
  if sha(out/name)!=provenance['outputs_sha256'][name]:raise ValueError('Replayed statistics differ from execution manifest: '+name)
 print(json.dumps({'status':'statistics rebuilt from public saved per-query results','rows':len(rows),'queries':len(ids)}))

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--summarize-saved',action='store_true',help='Rebuild statistics from saved public per-query results; no raw data/model download')
 ap.add_argument('--output',type=Path,default=ROOT/'revisions/v3/pipeline')
 ap.add_argument('--raw-test',type=Path,default=ROOT/'data/raw/qasper-test-and-evaluator-v0/qasper-test-v0.3.json')
 ap.add_argument('--raw-dev',type=Path,default=ROOT/'data/raw/qasper-train-dev-v0/qasper-dev-v0.3.json')
 ap.add_argument('--rankings',type=Path,default=ROOT/'reference_outputs/main_v1/rankings.jsonl')
 args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
 if args.summarize_saved:
  summarize_saved(out);return
 if not (out/'plan.json').exists():raise RuntimeError('Freeze selection/scoring plan before execution')
 started=datetime.datetime.now(datetime.timezone.utc).isoformat();cache=acquire(out/'source_cache/upstream')
 dataset,loader,metrics=load_upstream(cache)
 nativecache=out/'source_cache/native_cache';nativecache.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(args.raw_dev,nativecache/'qasper-dev-v0.3.json')
 native=loader.load_qasper(split='validation',max_papers=None,cache_dir=nativecache)
 wrapped=convert_supplied(loader,json.loads(args.raw_dev.read_text()))
 assert dataclasses.asdict(native)==dataclasses.asdict(wrapped), 'Data-supply wrapper disagrees on native dev'
 raw=json.loads(args.raw_test.read_text());converted=convert_supplied(loader,raw)
 # Save full real export privately, and publish text-free derivations below.
 save(out/'source_cache/test_export.json',dataclasses.asdict(converted))
 save(out/'export_qrels.json',converted.qrels)
 corpus_index=[{'id':pid,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'normalized_sha256':hashlib.sha256(normalized(text).encode()).hexdigest()} for pid,text in converted.corpus.items()]
 save(out/'export_corpus_index.json',corpus_index)
 # Verify the upstream JSONL export/reload path as well as the in-memory converter.
 questions=out/'source_cache/questions.jsonl';corpusfile=out/'source_cache/corpus.jsonl'
 questions.write_text(''.join(json.dumps(dataclasses.asdict(x),ensure_ascii=False)+'\n' for x in converted.examples))
 corpusfile.write_text(''.join(json.dumps({'id':p,'text':t},ensure_ascii=False)+'\n' for p,t in converted.corpus.items()))
 reloaded=dataset.load_jsonl(questions,corpusfile,out/'export_qrels.json',name='qasper')
 assert dataclasses.asdict(reloaded)==dataclasses.asdict(converted)
 xs,audit=qasper_instances(args.raw_test,'test');xs=sorted(xs,key=lambda x:x.id)
 assert len(xs)==875
 originals=load_jsonl(args.rankings);rank={(r['id'],r['method']):r for r in originals if r['dataset']=='qasper'}
 mappings=[];aligned=[];allids={x.id for x in xs}
 for x in xs:
  assert digest_data(dataclasses.asdict(x))==rank[x.id,'bm25']['instance_hash'], 'Original eligible instance hash changed'
  mapping,ambiguity=normalized_alignment(x,converted.corpus);u=set().union(*map(set,x.gold))
  source_ids={mapping[i] for i in u if i in mapping};export_ids=set(converted.qrels.get(x.id,{}))
  cat=membership_category(source_ids,export_ids,len(mapping)==len(x.units))
  kept=x.id in converted.qrels;distinct=topology(x.gold)['n_distinct_sets']
  row={'id':x.id,'paper_id':x.cluster,'source_units':len(x.units),'mapped_units':len(mapping),'all_candidates_mapped':len(mapping)==len(x.units),'exported_query':kept,'source_union_size':len(u),'export_membership_size':len(export_ids),'membership_category':cat,'distinct_evidence_sets':distinct,'representation':'flat_only','group_relationship_loss':distinct>1,'candidate_scope':'controlled normalized-text images of original paper-body candidates; canonical IDs may denote identical abstract text; full upstream export additionally pools other units and papers','export_extra_candidate_ids':sum(p.split('::',1)[0]==x.cluster for p in converted.corpus)-len(mapping),'mapped_source_union':sorted(source_ids),'export_membership':sorted(export_ids),'unit_mapping':{str(i):v for i,v in mapping.items()},'normalized_text_ambiguities':{str(i):v for i,v in ambiguity.items()}}
  missing_evidence=[]
  qa=next(q for q in raw[x.cluster]['qas'] if q['question_id']==x.id)
  exact_texts={text for pid,text in converted.corpus.items() if pid.split('::',1)[0]==x.cluster}
  for unit_id in sorted(source_ids-export_ids):
   i=next(i for i,pid in mapping.items() if pid==unit_id)
   annotations=[e for a in qa['answers'] for e in a['answer'].get('evidence',[]) if normalized(e)==x.units[i]]
   missing_evidence.append({'source_unit_index':i,'mapped_export_id':unit_id,
    'annotation_evidence_sha256':[hashlib.sha256(e.encode()).hexdigest() for e in annotations],
    'any_stripped_evidence_exactly_matches_export_text':any(e.strip() in exact_texts for e in annotations),
    'normalized_match_to_source_unit':all(normalized(e)==x.units[i] for e in annotations),
    'reason':'strip-only converter misses whitespace-normalized source match' if not any(e.strip() in exact_texts for e in annotations) else 'export ID selection differs'})
  row['missing_membership_evidence']=missing_evidence
  mappings.append(row)
  if kept and cat=='exact_union_membership' and len(set(mapping.values()))==len(x.units):aligned.append((x,mapping))
 save(out/'main_cohort_alignment.json',mappings)
 rawrows=[]
 for pid,paper in raw.items():
  bytext={}
  for unitid,text in converted.corpus.items():
   if unitid.split('::',1)[0]==pid:bytext.setdefault(text,unitid)
  for qa in paper['qas']:
   qid=qa['question_id'];ev={e.strip() for a in qa['answers'] for e in a['answer'].get('evidence',[])}
   missing=[e for e in ev if e not in bytext];source_ids={bytext[e] for e in ev if e in bytext}
   cat='not_exported' if qid not in converted.qrels else ('unmapped_source_evidence' if missing else membership_category(source_ids,converted.qrels[qid]))
   rawrows.append({'id':qid,'paper_id':pid,'in_original_875':qid in allids,'category':cat,'no_mapped_evidence':not source_ids,'no_scorable_answer':not any(loader._qasper_answer(a['answer']) for a in qa['answers']),'distinct_raw_evidence_strings':len(ev),'unmatched_raw_evidence_strings':len(missing),'export_membership_size':len(converted.qrels.get(qid,{}))})
 write_csv(out/'all_raw_question_flow.csv',rawrows)
 # Real source scorer, with strict monotonically decreasing artificial rank scores.
 # This preserves the frozen order including its original unit-index tie break.
 qrels={x.id:converted.qrels[x.id] for x,mapping in aligned};clusters=[x.cluster for x,mapping in aligned]
 boot=bootstrap_matrix(clusters);per_item=[];summary=[];per_method={};max_error=0.
 for method in METHODS:
  run={}
  for x,mapping in aligned:
   order=rank[x.id,method]['ranking'];assert sorted(order)==list(range(len(x.units)))
   run[x.id]={mapping[i]:float(len(order)-j) for j,i in enumerate(order)}
  aggregate=metrics.retrieval_metrics(qrels,run)
  per={metric:metrics.retrieval_metrics_per_query(qrels,run,metric) for metric in MEASURES}
  save(out/f'run_{method}.json',run)
  rows=[]
  for x,mapping in aligned:
   r=rank[x.id,method];order=r['ranking'];ids=[mapping[i] for i in order]
   values=score(order[:5],x.gold);v5=conventional(ids,qrels[x.id],5);v10=conventional(ids,qrels[x.id],10)
   expected={'nDCG@10':v10['ndcg'],'R@5':v5['recall'],'R@10':v10['recall'],'Success@5':v5['success'],'Success@10':v10['success'],'RR@10':v10['rr']}
   for key,value in expected.items():max_error=max(max_error,abs(per[key][x.id]-value))
   assert abs(per['R@5'][x.id]-values['union_recall'])<1e-12
   assert per['Success@5'][x.id]==values['hit']
   row={'id':x.id,'paper_id':x.cluster,'method':method,'k':5,**{m:per[m][x.id] for m in MEASURES},**values}
   rows.append(row);per_item.append(row)
  per_method[method]=rows
  for m in MEASURES+list(values):
   mean,ci=estimate([r[m] for r in rows],boot)
   summary.append({'method':method,'n':len(rows),'clusters':len(set(clusters)),'metric':m,'mean':float(mean[0]),'lo':float(ci[0,0]),'hi':float(ci[0,1]),'status':'revision-added exploratory'})
  for m in MEASURES:
   assert abs(aggregate[m]-np.mean([r[m] for r in rows]))<1e-12
 assert max_error<1e-12
 write_csv(out/'per_query_scores.csv',per_item);write_csv(out/'score_summary.csv',summary)
 contrasts=[]
 for metric in ['R@5','Success@5','nDCG@10','RR@10','complete','union_complete','max_f1','union_f1']:
  a=per_method['dense'];b=per_method['bm25'];values=[x[metric]-y[metric] for x,y in zip(a,b)]
  m,ci=estimate(values,boot)
  contrasts.append({'contrast':'MiniLM minus BM25','metric':metric,'n':len(values),'mean':float(m[0]),'lo':float(ci[0,0]),'hi':float(ci[0,1]),'status':'revision-added exploratory'})
 write_csv(out/'paired_contrasts.csv',contrasts)
 environment={d:importlib.metadata.version(d) for d in ['ir-measures','pytrec-eval-terrier','numpy','pandas','scikit-learn','scipy']}
 report={'status':'completed revision-added exploratory conversion/scoring replay','started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'upstream':f'https://github.com/{UPSTREAM}/tree/{REVISION}','upstream_source_hashes':FILES,'upstream_code_locations':{'converter':'src/sage/eval/benchmarks.py:99-159','export_reload':'src/sage/eval/dataset.py:127-147','scorer':'src/sage/eval/metrics.py:28-54'},'source_code_sha256':sha(__file__),'input_hashes':{'qasper_test':sha(args.raw_test),'qasper_dev':sha(args.raw_dev),'frozen_rankings':sha(args.rankings)},'environment':{'python':platform.python_version(),'platform':platform.platform(),**environment},'native_dev':{'queries':len(native.examples),'corpus_units':len(native.corpus),'unchanged_loader_vs_data_supply_wrapper_exact_equality':True,'serialized_output_sha256':digest_data(dataclasses.asdict(native))},'test_export':{'raw_questions':len(rawrows),'papers':len(raw),'queries':len(converted.examples),'corpus_units':len(converted.corpus),'raw_flow':dict(collections.Counter(r['category'] for r in rawrows)),'not_exported_reasons':{'no_mapped_evidence':sum(r['category']=='not_exported' and r['no_mapped_evidence'] for r in rawrows),'no_scorable_answer':sum(r['category']=='not_exported' and r['no_scorable_answer'] for r in rawrows),'both':sum(r['category']=='not_exported' and r['no_mapped_evidence'] and r['no_scorable_answer'] for r in rawrows)},'upstream_jsonl_roundtrip_exact_equality':True},'main_cohort':{'original_n':len(xs),'original_papers':len(set(x.cluster for x in xs)),'scored_n':len(aligned),'scored_papers':len(set(clusters)),'excluded_n':len(xs)-len(aligned),'membership_counts':dict(collections.Counter(r['membership_category'] for r in mappings)),'queries_not_exported':sum(not r['exported_query'] for r in mappings),'exact_membership_any_text_ambiguity_questions':sum(r['membership_category']=='exact_union_membership' and bool(r['normalized_text_ambiguities']) for r in mappings),'exact_membership_gold_text_ambiguity_questions':sum(r['membership_category']=='exact_union_membership' and any(r['unit_mapping'][i] in r['mapped_source_union'] for i in r['normalized_text_ambiguities']) for r in mappings),'exact_membership_abstract_id_mapping_questions':sum(r['membership_category']=='exact_union_membership' and any(pid.split('::')[1]=='0' for pid in r['unit_mapping'].values()) for r in mappings),'exact_membership_abstract_gold_id_mapping_questions':sum(r['membership_category']=='exact_union_membership' and any(pid.split('::')[1]=='0' for pid in r['mapped_source_union']) for r in mappings),'exact_union_multiset_questions':sum(r['membership_category']=='exact_union_membership' and r['distinct_evidence_sets']>1 for r in mappings),'exact_union_one_distinct_set_questions':sum(r['membership_category']=='exact_union_membership' and r['distinct_evidence_sets']==1 for r in mappings),'candidate_scope_change_count':len(mappings),'ambiguity_question_count':sum(bool(r['normalized_text_ambiguities']) for r in mappings),'missing_unit_reasons':dict(collections.Counter(e['reason'] for r in mappings for e in r['missing_membership_evidence']))},'validation':{'all_five_rankings_complete_permutations':True,'real_scorer_formula_max_absolute_error':max_error,'real_recall_equals_union_recall':True,'real_success_equals_H':True,'scoring_runs':len(per_item),'bootstrap_replicates':10000,'bootstrap_seed':20261002,'cluster_unit':'paper; cluster resampling with item-weighted denominator'},'interpretation':'The flat target does not preserve which evidence groups were accepted. Upstream explicitly evaluates graded relevance, recall, success and reciprocal rank; its code does not claim C or A, and no objective/implementation mismatch is established. Actual converter and scorer execute; native dev identity validates data-supply interface, test is a documented interface extension. Controlled rankings retain the original normalized body-text units and exclude abstract-only text and other-paper distractors; first-match canonical IDs can denote abstract text identical to a body unit; this is not a reproduction of full pooled retrieval, RAPTOR, generation, or published downstream scores.'}
 save(out/'report.json',report)
 (out/'requirements.txt').write_text(''.join(f'{k}=={v}\n' for k,v in environment.items()))
 (out/'README.md').write_text('# Real conversion and scoring replay\n\nRevision-added exploratory analysis. Read `plan.json` before results.\n\nRun `python src/revision_v3_pipeline.py --summarize-saved` to rebuild statistics from public per-query scores without raw data, model weights, upstream source or ir_measures.\n\nRun `python src/revision_v3_pipeline.py` after acquiring the original data and installing `requirements.txt`. It fetches three hash-pinned upstream source files into ignored `source_cache/`; full source-text exports stay there. Public outputs contain source IDs, text hashes, qrels, mappings, frozen-rank scorer inputs and derived results. The unchanged native dev loader and the injected data-only wrapper produce identical structures. The same converter then consumes the real frozen test input.\n\nThe upstream dataset module is isolated by dropping two unused imports for indexing types; its dataclasses and file loader, and the converter and scorer functions, are executed without body changes. The original upstream `load_jsonl` reloads the actual export exactly. The source scorer uses ir_measures/pytrec_eval; all six measures agree with direct formulas. Retrieval score ties are replaced by strictly decreasing rank values to preserve original deterministic order.\n\nThe upstream task pools abstracts and body paragraphs across papers. Controlled replay uses the normalized-text images of original paper-body units and the five saved rankings. The first matching export ID is canonical: 8 of 866 aligned questions map at least one body text to an identical abstract text ID (one involves gold); 90 have duplicate or normalized-equivalent export texts (four involve gold). This is an explicit quotient by original normalized text, not a one-to-one match to raw paragraph occurrences. Abstract-only text and other-paper distractors remain outside the controlled rankings. This scope change is explicit for every item. Exact source-union/qrels membership is a separate axis and must not be confused with identical full task semantics. No whole downstream system, generation, or original published performance is reproduced.\n\nThe upstream code documents standard relevance objectives; flat qrels are not A. C/A and overlap scores here are additional annotation-defined contrasts. Lack of grouped output prevents generally reconstructing C, while the implemented original relevance measures remain appropriate to their stated target.\n')
 output_names=['report.json','all_raw_question_flow.csv','export_qrels.json','export_corpus_index.json','main_cohort_alignment.json','per_query_scores.csv','score_summary.csv','paired_contrasts.csv']+[f'run_{m}.json' for m in METHODS]
 save(out/'manifest.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'revision-added exploratory executed conversion/scoring outputs','source_code_sha256':sha(__file__),'selection_plan_sha256':sha(out/'plan.json'),'upstream_source_hashes':FILES,'input_hashes':report['input_hashes'],'environment':report['environment'],'outputs_sha256':{name:sha(out/name) for name in output_names},'scope':'Manifest records completed outputs; excludes itself, diagnostic logs and subsequent review reports to avoid self-reference.'})
 print(json.dumps(report,indent=2))

if __name__=='__main__':main()

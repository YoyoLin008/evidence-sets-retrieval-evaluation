"""Deterministic revision-added exploratory real annotation panels (no human audit)."""
from __future__ import annotations
import argparse, dataclasses, datetime, hashlib, json
from pathlib import Path
from evidence import ROOT, qasper_instances, scifact_instances, load_jsonl, topology, score, normalized, digest

NEW_ID='0bde3ecfdd7c4a9af23f53da2cda6cd7a8398220'

def eligible(instance,ranking):
 t=topology(instance.gold);s=score(ranking[:5],instance.gold)
 return (instance.dataset=='qasper' and instance.metadata['answer_agreement'] and
         t['n_minimal_sets']>=2 and t['n_minimal_sets']==t['n_distinct_sets'] and
         s['complete']==1 and s['union_complete']==0)

def select(instances,rankings):
 candidates=[x for x in instances if eligible(x,rankings[x.dataset,x.id]['ranking'])]
 return sorted(candidates,key=lambda x:hashlib.sha256(x.id.encode()).hexdigest())

def source_positions(paper,unit):
 out=[];ordinal=0
 for section_index,s in enumerate(paper['full_text']):
  for paragraph_index,text in enumerate(s['paragraphs']):
   if normalized(text):
    if normalized(text)==unit:out.append({'section_index':section_index,'section_name':s.get('section_name'),'paragraph_index':paragraph_index,'nonempty_body_ordinal':ordinal})
    ordinal+=1
 return out

def answer_text(a):
 if a.get('extractive_spans'):return ', '.join(a['extractive_spans'])
 if a.get('free_form_answer'):return a['free_form_answer']
 if a.get('yes_no') is not None:return 'yes' if a['yes_no'] else 'no'
 return ''

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,default=ROOT/'revisions/v3/examples');args=ap.parse_args();out=args.output
 if not (out/'plan.json').exists():raise RuntimeError('Freeze deterministic selection before inspecting results')
 qpath=ROOT/'data/raw/qasper-test-and-evaluator-v0/qasper-test-v0.3.json'
 qasper=json.loads(qpath.read_text());qx,_=qasper_instances(qpath,'test')
 sx,_=scifact_instances(ROOT/'data/raw/scifact/data/claims_dev.jsonl',ROOT/'data/raw/scifact/data/corpus.jsonl','dev')
 instances=qx+sx;ix={(x.dataset,x.id):x for x in instances}
 ranks={(r['dataset'],r['id']):r for r in load_jsonl(ROOT/'reference_outputs/main_v1/rankings.jsonl') if r['method']=='bm25'}
 candidates=select(qx,ranks);old=json.loads((ROOT/'analysis/representative_examples.json').read_text())
 selected=[(next(x for x in old if x['dataset']==d and x['category']=='one_not_union'),'retained preselected '+d+' case') for d in ['qasper','scifact']]
 if candidates:selected.insert(1,({'dataset':'qasper','id':candidates[0].id},'new agreement/no-superset hash-selected case'))
 panels=[]
 # Short exact excerpts verified against the raw evidence units below. They are
 # examples, not claims that text reading validates all annotation alternatives.
 excerpts={
 ('qasper','14fdc8087f2a62baea9d50c4aa3a3f8310b38d17'):{17:'Experiments were performed using the CHiME-5 data.',22:'An extensive set of experiments',23:'the recognition accuracy improves monotonically',34:'CHiME-5 dinner party data'},
 ('qasper',NEW_ID):{20:'aligned complex-simple sentence pairs from English Wikipedia',24:'the output is grammatical English'},
 ('scifact','873:1180972'):{3:'body mass index (kg/m2) significantly increased',4:'a steady but weaker increase',6:'a striking, significant increase',7:'influenced by genetic factors independent of sex'},
 }
 interpretation={
 '14fdc8087f2a62baea9d50c4aa3a3f8310b38d17':'The singleton {23} is nested within {17,22,23,34}; completing the singleton makes C=1 before the full union is covered. The two recorded normalized answers differ. This illustrates annotation nesting and answer-text variation, not same-answer alternative sufficient evidence.',
 NEW_ID:'All three recorded answers normalize to English; duplicate {24} leaves two distinct singleton alternatives, {20} and {24}, with no nesting. Paragraph 20 describes English Wikipedia pairs, whereas paragraph 24 mentions grammatical English as a fluency criterion. The selected first case is retained despite this difference in how directly the paragraphs support the question. It demonstrates annotation-defined same-answer alternatives; no independent human judgment establishes semantic sufficiency of either singleton.',
 '873:1180972':'The gold label is CONTRADICT and the family contains the two-sentence set {3,4} plus alternatives {6} and {7}. The retrieved prefix completes {7}, while {6} and {3,4} remain incomplete. This is an annotation-defined alternative-rationale control; completion is not a new semantic validation.'}
 for selected_item,role in selected:
  key=(selected_item['dataset'],selected_item['id']);x=ix[key];r=ranks[key];assert digest(dataclasses.asdict(x))==r['instance_hash'];k=5 if x.dataset=='qasper' else 3;prefix=r['ranking'][:k]
  selected_units=sorted(set(sum(x.gold,[]))|set(prefix));units=[]
  for i in selected_units:
   unit={'index':i,'source_id':f'{x.cluster}:paragraph:{i}' if x.dataset=='qasper' else f"{x.metadata['doc_id']}:sentence:{i}",'text_sha256':hashlib.sha256(x.units[i].encode()).hexdigest()}
   if x.dataset=='qasper':unit['raw_source_positions']=source_positions(qasper[x.cluster],x.units[i]);assert unit['raw_source_positions']
   else:unit['sentence_index']=i
   excerpt=excerpts[key].get(i)
   if excerpt:assert excerpt in x.units[i];unit['short_verbatim_excerpt']=excerpt
   units.append(unit)
  p={'status':'revision-added exploratory presentation','role':role,'dataset':x.dataset,'id':x.id,'paper_or_document_id':x.cluster if x.dataset=='qasper' else x.metadata['doc_id'],'query':x.query,'gold':x.gold,'distinct_sets':[list(g) for g in sorted(set(tuple(e) for e in x.gold))],'ranking_prefix':prefix,'completed_reference_sets':[e for e in x.gold if set(e)<=set(prefix)],'method':'bm25','k':k,'scores':score(prefix,x.gold),'costs':r['costs'],'topology':topology(x.gold),'strict_normalized_answer_agreement':x.metadata['answer_agreement'],'units':units,'source_unit_index_base':0,'interpretation':interpretation[x.id],'human_semantic_validation':False}
  if x.dataset=='qasper':
   qa=next(q for q in qasper[x.cluster]['qas'] if q['question_id']==x.id)
   answers=[answer_text(a['answer']) for a in qa['answers']]
   p['answer_normalized_keys']=x.metadata['answer_keys'];p['raw_answer_sha256']=[hashlib.sha256(a.encode()).hexdigest() for a in answers]
   p['answer_display']=answers if x.id==NEW_ID else ['Paraphrase: an extensive experimental evaluation on difficult CHiME-5 dinner-party data.','Paraphrase: training enhancement improves accuracy provided it is no stronger than test enhancement.']
   p['source_url']='https://arxiv.org/abs/'+x.cluster
  else:p['label']=x.metadata['label'];p['claim_id']=x.metadata['claim_id'];p['source_url']='https://github.com/allenai/scifact';p['source_record']='data/corpus.jsonl doc_id='+x.metadata['doc_id']
  p['quoted_evidence_word_count']=sum(len(u.get('short_verbatim_excerpt','').split()) for u in units)
  assert p['quoted_evidence_word_count']<=25
  panels.append(p)
 report={'status':'completed revision-added exploratory examples','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'known_outcomes':'All original outcomes were visible; new example is explicitly selected on C=1,A=0, so illustrates the mechanism without estimating semantic prevalence.','new_candidate_count':len(candidates),'new_candidate_ids_hash_order':[{'id':x.id,'sha256':hashlib.sha256(x.id.encode()).hexdigest()} for x in candidates],'selected_new_id':candidates[0].id if candidates else None,'selected_first_without_substitution':True,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'original_qasper_case_retained':True,'original_scifact_case_retained':True,'panels':panels}
 (out/'panels.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 text=['# Real annotation panels','', 'Revision-added exploratory presentation. Unit indexes are zero-based. Short quotations reproduce annotation-source text; full passages are not republished. All other evidence discussion is paraphrase. No new human semantic annotation was performed.','',f'The new QASPER selection had {len(candidates)} eligible questions. The first SHA-256 ID was retained, with known original outcomes and no substitution.','']
 for p in panels:
  text += [f"## {p['role']}",'',f"Source: {p['id']} / {p['paper_or_document_id']}.",f"Question/claim: {p['query']}",f"Answers/label: {p.get('answer_display',p.get('label'))}",f"Original evidence family: {p['gold']}; exact BM25 prefix at k={p['k']}: {p['ranking_prefix']}.",f"H/C/A = {p['scores']['hit']}/{p['scores']['complete']}/{p['scores']['union_complete']}; d_C={p['costs']['depth_complete']}, d_A={p['costs']['depth_union']}.",'']
  for u in p['units']:
   if 'short_verbatim_excerpt' in u:text.append(f"- {u['source_id']}: “{u['short_verbatim_excerpt']}”")
  text+=['',p['interpretation'],'']
 (out/'panels.md').write_text('\n'.join(text))
 print(json.dumps({k:v for k,v in report.items() if k not in ['panels','new_candidate_ids_hash_order']},indent=2))

if __name__=='__main__':main()

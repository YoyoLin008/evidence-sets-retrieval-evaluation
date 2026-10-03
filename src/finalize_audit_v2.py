"""Build a bounded audit ledger from pinned sources and explicit adjudications."""
from pathlib import Path
import json,hashlib,datetime,csv,ast,copy,io,logging,types
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'revisions/v2/audit'
# index: class, source granularity, output/target, transformation, limitation
DEC={
97:('other_not_applicable','paper/paragraph evidence','answer generation','SCROLLS input/output loader passes full text and answer strings to generation metrics.','Evidence-set completion is outside this task.'),
91:('both_exposed','paragraph sets','paragraph labels and reference-aware evaluator','convert_qasper unions mapped non-float evidence into paragraph labels; vendored official evaluator retains answer-specific evidence and maximizes reference F1.','Union fixture uses uniquely mapped text; floats/empty annotations are filtered.'),
112:('flat_only','QASPER paragraphs/abstract passages','passage qrels','Distribution exposes query-id/corpus-id/score only. Corpus identity check matches 20,098 of 20,508 texts to original body paragraphs and all 1,335 query IDs.','Only 576/1,335 query targets equal the raw evidence union. Conversion code not exposed here; no exact union-preserving intervention is claimed for the distribution.'),
117:('other_not_applicable','paragraph evidence sets','chunks and character-span extraction','evidence_for_question aggregates annotations; output labels evaluate chunk/span extraction.','Aggregation exists, but the span/chunk target changes granularity and task.'),
90:('other_not_applicable','QASPER evidence annotations','SCROLLS answer generation','SCROLLS evaluates input/output answer strings with answer metrics.','Answer-only task, not an evidence-completion evaluation.'),
116:('other_not_applicable','paragraph/span references','one contiguous sentence span','aggregate_question_spans aggregates evidence locations and chooses one contiguous span.','Selection and granularity change are not union-preserving flattening.'),
99:('preserved','paragraph evidence sets per answer','same nested answer/evidence structure','_generate_examples yields source paper objects with their nested answer annotations.','Schema and isolated loader fixture checked; no end-to-end model executed.'),
92:('other_not_applicable','QASPER source schema','answer F1 prompt','Task registers F1 for generated gold answers.','Prompt fields differ from native QASPER fields; missing alignment step prevents an end-to-end runtime claim.'),
98:('other_not_applicable','LongBench derivative of QASPER','answer QA F1','Prediction uses context and answers; evaluation maps QASPER to qa_f1_score.','Generation task and upstream LongBench lineage; no evidence-family output expected.'),
110:('other_not_applicable','paragraph evidence','sentence relevance','Collects answer evidence and maps paragraphs to split sentence IDs before precision/recall.','Paragraph-to-sentence conversion changes retrieval granularity.'),
123:('flat_only','paragraph evidence sets','paragraph qrels and IR metrics','load_qasper maps each annotation evidence string to paragraph IDs and accumulates one qrels dictionary; answers have no membership linkage.','Unmatched evidence is omitted; exact union preservation is established on a fully mappable synthetic fixture, not claimed for all raw items.'),
119:('other_not_applicable','QASPER papers','PDF document-injection/response task','README documents scientific-paper PDF generation and injected-document experiments.','Question/rationale completion is not this task; evaluate.py is not a QASPER evidence scorer.'),
105:('other_not_applicable','paragraph evidence sets','first-reference snippets','_first_evidence selects the first answerable reference; convert filters unmapped and short snippets.','Intentional reference selection changes the accepted family and may delete units.'),
59:('undetermined','untraced QASPER derivative','question/answer/context list','Parquet schema contains a flat list of context strings and no annotation grouping.','No converter, source IDs, or evaluator is exposed; cannot establish whether contexts are gold evidence or which granularity/selection produced them.'),
49:('both_exposed','answer-specific paragraph evidence','flat evidence plus answer-evidence pairs','QasperAdapter retains answer_evidence_pairs in metadata and accumulates a deduplicated evidence list; recall helper uses flat text matching.','Pairs require a usable answer. Shared loader lineage with OpenViking, counted once; prompt differences do not create a second conversion lineage.'),
83:('other_not_applicable','BEIR document qrels','document retrieval','BEIR GenericDataLoader supplies document corpus/queries/qrels to standard retrieval metrics.','No sentence-rationale grouping enters the inspected task.'),
129:('preserved','sentence rationale sets','one row per claim/document/rationale','_generate_examples emits each rationale as its own evidence_sentences list with claim/document IDs.','Regrouping rows recovers the family; explicit set-ID column is unnecessary.'),
146:('other_not_applicable','BEIR queries','150 sampled query records','Dataset card gives seed-0 sampling of 150 BEIR SciFact queries.','Query-only distribution; it does not convert rationale sets.'),
82:('other_not_applicable','BEIR document qrels','document retrieval','BEIR loader feeds document relevance metrics.','Document IDs do not denote rationale sentences.'),
128:('other_not_applicable','BEIR document qrels','document retrieval','download_data obtains BEIR SciFact; evaluation uses document qrels and ranking metrics.','Document-retrieval task.'),
79:('other_not_applicable','SciFact document IDs','document qrels','All 339 test qrels corpus IDs join original SciFact document IDs.','Upstream translation/converter unspecified; ID join establishes document rather than sentence granularity only.'),
81:('other_not_applicable','BEIR document qrels','document retrieval','Loader downloads BEIR corpus/queries/qrels and returns relevant_doc_ids to retrieval metrics.','No evidence-set input in inspected pipeline.'),
80:('other_not_applicable','BEIR document qrels','document retrieval','Loader reads corpus/queries/qrels and returns gold_doc_ids to retrieval metrics.','Same task as another JeV project but distinct package/source; common task alone is not proof of a fork.'),
143:('other_not_applicable','BEIR document qrels','document qrels','Pinned provenance records normalized BEIR/MTEB corpus/query/qrels copies.','Column normalization does not establish sentence-rationale flattening.'),
138:('other_not_applicable','BEIR document qrels','query and expected document matches','Parquet expected_output encodes document IDs and relevance scores.','Document-level representation.'),
75:('other_not_applicable','BEIR document collection','document retrieval','Anserini reproduction configuration uses SciFact document qrels.','The word flat in the collection filename is not evidence of rationale-set loss.'),
42:('other_not_applicable','BEIR document qrels','decontaminated document subset','Dataset exposes document corpus/query/qrels subsets for retrieval.','Filtering and document target differ from sentence-family intervention.'),
127:('other_not_applicable','SciFact-Open claim/document labels','open document fact verification','run_eval consumes evidence-document labels on expanded SciFact-Open data.','Different benchmark and target; not original sentence-rationale completion.'),
130:('preserved','sentence rationale sets','source evidences and text pairs','Source configuration retains evidence objects with document and sentence_ids; BigBio text-pair path constructs each rationale group separately.','Alternative text-pair task changes output type, but source family remains available.'),
65:('both_exposed','sentence rationale sets','structured Claim and flattened text helper','Claim.evidence preserves raw doc-to-rationale lists; get_evidence_sentences concatenates rationale sentences per document.','Document retrieval metrics are a separate objective; the helper does not prove a faulty final evaluator.')}

# Official AllenAI distributions belong to benchmark reference families, per protocol.
DEC.pop(99);DEC.pop(129)
DEC[89]=('both_exposed','paragraph evidence sets','union paragraph classification and best-reference evidence F1','QasperEvidencePromptReader unions evidence into paragraph Yes/No labels; standalone evaluation reloads each original reference and selects maximal F1.','Substring matching may expand membership; the grouped evaluator path prevents family-wide information loss.')
DEC[139]=('other_not_applicable','translated BEIR document qrels','Persian document retrieval','Pinned card describes translated SciFact BEIR abstracts; test qrels retain document IDs.','Translation and document-level target are not sentence-rationale flattening.')

def extract(path,name):
 tree=ast.parse(path.read_text());nodes=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name];assert len(nodes)==1
 n=copy.deepcopy(nodes[0]);n.decorator_list=[]
 # Isolate the reviewed function; defer annotations, do not import/run project entrypoints.
 mod=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),n],type_ignores=[]);return compile(ast.fix_missing_locations(mod),str(path),'exec')
def main():
 pins={r['index']:r for r in json.loads((A/'pins.json').read_text())};fm=json.loads((A/'file_manifest.json').read_text());sel=json.loads((A/'selected_families.json').read_text())
 def file(i,suffix):return A/pins[i]['directory']/'files'/suffix
 fixture=[]
 fam1=[['a','b'],['c']];fam2=[['a'],['b','c']]
 def qdata(family):return {'paper':{'title':'title','abstract':'abstract','full_text':[{'section_name':'section','paragraphs':['a','b','c']}],'qas':[{'question_id':'q','question':'question','answers':[{'answer':{'evidence':e,'free_form_answer':'answer','unanswerable':False}} for e in family]}]}}
 # 1: QASPER raw loader preserves grouped references.
 env={'json':json,'logger':logging.getLogger('fixture')};exec(extract(file(99,'qasper.py'),'_generate_examples'),env)
 obj=list(env['_generate_examples'](None,'data',[('data',io.BytesIO(json.dumps(qdata(fam1)).encode()))]))[0][1]
 assert [a['answer']['evidence'] for a in obj['qas'][0]['answers']]==fam1
 fixture.append({'index':99,'check':'nested references survive loader','passed':True})
 # 2: SciFact row expansion is reversible at claim/document granularity.
 ev={'id':1,'claim':'claim','cited_doc_ids':[7],'evidence':{'7':[{'sentences':e,'label':'SUPPORT'} for e in [[0,1],[2]]]}}
 env={'json':json};exec(extract(file(129,'scifact.py'),'_generate_examples'),env)
 rows=list(env['_generate_examples'](types.SimpleNamespace(config=types.SimpleNamespace(name='claims')),'data','dev',[('data',[json.dumps(ev).encode()])]))
 assert [r['evidence_sentences'] for _,r in rows]==[[0,1],[2]];assert all(r['id']==1 and r['evidence_doc_id']=='7' for _,r in rows)
 fixture.append({'index':129,'check':'rationale rows regroup without loss','passed':True})
 # 3: Two different fully mappable evidence families collapse to identical qrels.
 env={'Path':Path,'QAExample':lambda **k:k,'RetrievalDataset':lambda **k:k};exec(extract(file(123,'src/sage/eval/benchmarks.py'),'_qasper_answer'),env);exec(extract(file(123,'src/sage/eval/benchmarks.py'),'load_qasper'),env)
 results=[]
 for f in [fam1,fam2]:
  env['_qasper_json']=lambda *args,f=f:qdata(f);results.append(env['load_qasper']())
 assert results[0]['qrels']==results[1]['qrels']=={'q':{'paper::1::0':1,'paper::1::1':1,'paper::1::2':1}}
 assert results[0]['examples']==results[1]['examples']
 fixture.append({'index':123,'check':'distinct families yield identical paragraph qrels while retaining every fixture unit','passed':True,'input_families':[fam1,fam2],'output':results[0]['qrels']})
 # 4: CGSN reviewed converter, simple word tokenization stub (fixture has only single words).
 env={'copy':copy,'tqdm':lambda x,**kw:x,'nltk':types.SimpleNamespace(word_tokenize=lambda x:x.split())};path=file(91,'create_qasper_examples_scibert.py');exec(extract(path,'text_clean'),env);exec(extract(path,'convert_qasper'),env)
 a,b=[env['convert_qasper'](qdata(f)) for f in [fam1,fam2]];assert a==b and len(a[0]['annotations'])==3
 fixture.append({'index':91,'check':'training converter discards family linkage; tokenizer stub does not change these single-word inputs','passed':True})
 # 5: First reference is selected, not the union.
 env={'_FLOAT_PREFIX':'FLOAT SELECTED:'};exec(extract(file(105,'scripts/benchmarks/prepare_qasper.py'),'_first_evidence'),env);out=env['_first_evidence'](qdata(fam1)['paper']['qas'][0]);assert out==['a','b']
 fixture.append({'index':105,'check':'first-reference selection distinguished from union conversion','passed':True,'output':out})
 # 6: Structured claim survives beside flattening helper.
 env={};exec(extract(file(65,'src/data/dataset_loader.py'),'get_evidence_sentences'),env);claim=types.SimpleNamespace(evidence=copy.deepcopy(ev['evidence']));loader=types.SimpleNamespace(get_document=lambda i:types.SimpleNamespace(abstract=['a','b','c']))
 assert env['get_evidence_sentences'](loader,claim)=={7:['a','b','c']} and claim.evidence==ev['evidence']
 fixture.append({'index':65,'check':'flat helper and intact structured input coexist','passed':True})
 (A/'fixture_results.json').write_text(json.dumps(fixture,indent=2))
 # Deduplicate late-established OpenViking lineage; retain first-discovered identifier.
 correction={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_selection_preserved':'selected_families.json','indices_merged':[49,52],'canonical_retained':pins[49]['canonical'],'rule':'First-discovered identifier retained within this newly established lineage. Its selected representative was already index 49; no selected representative changes.','evidence':'openviking_lineage_check.json: adapter conversion body identical; differences confined to imports and prompt text.','eligible_counts_corrected':{'QASPER':24,'SciFact':32},'official_reference_correction':{'excluded_downstream_indices':[99,129],'replacement_indices':[89,139],'rule':'Official dataset distributions were mistakenly counted downstream in the first pass. Apply original reference-case exclusion, then take the next SHA-256-ranked eligible family in each benchmark. Correction is post-inspection and disclosed.'},'limitation':'Lineage and reference-case corrections were established after initial selection and some code inspection; original freeze and first-pass counts retained, not rewritten.'}
 (A/'lineage_correction.json').write_text(json.dumps(correction,indent=2))
 corrected=[r for r in sel if r['index'] not in [52,99,129]]
 for b in ['QASPER','SciFact']:
  for rank,r in enumerate(sorted([r for r in corrected if r['benchmark']==b],key=lambda r:r['selection_hash']),1):r['corrected_selection_rank']=rank;r['corrected_selected']=rank<=15
 assert {r['index'] for r in corrected if r['corrected_selected']}==set(DEC)
 (A/'selected_families_corrected.json').write_text(json.dumps(corrected,indent=2))
 ledger=[]
 for r in sorted([r for r in corrected if r['corrected_selected']],key=lambda x:(x['benchmark'],x['corrected_selection_rank'])):
  i=r['index'];cl,gran,target,trans,limit=DEC[i];pin=pins[i];sources=[x for x in fm if x['index']==i];evidence=[]
  for s in sources:
   p=A/s['local'];assert p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==s['sha256']
   evs=dict(path=s['path'],url=s['url'],sha256=s['sha256'])
   if p.suffix in ['.py','.md','.yaml','.tsv']:
    lines=p.read_text().splitlines();hits=[n for n,l in enumerate(lines,1) if any(w in l.lower() for w in ['evidence','qrels','gold','f1','recall','qasper','scifact','expected_output'])]
    evs['supporting_lines']=hits[:70];evs['line_count']=len(lines)
   else:evs['location']='schema/rows; see schema-check JSON where applicable'
   evidence.append(evs)
  ledger.append(dict(index=i,benchmark=r['benchmark'],canonical=r['canonical'],revision=pin['revision'],classification=cl,source_granularity=gran,output_target=target,transformation=trans,limitations=limit,evidence=evidence,verification='isolated conversion fixture + static trace' if any(f['index']==i for f in fixture) else 'static code/data-schema trace; no full pipeline execution',all_observed_units_retained=('yes on fully mapped fixture; raw filtering documented' if i in [91,123] else 'yes in grouped source path' if i in [99,129,130,65] else 'not established or not applicable'),second_pass='Same producing agent reread source/target roles, checked pinned bytes, and corrected category boundaries; not independent annotation',status='exploratory_post_main'))
 classes=['preserved','flat_only','both_exposed','other_not_applicable','undetermined'];counts={b:{c:sum(r['benchmark']==b and r['classification']==c for r in ledger) for c in classes} for b in ['QASPER','SciFact']}
 (A/'classification_ledger.json').write_text(json.dumps(ledger,indent=2));(A/'counts.json').write_text(json.dumps({'status':'exploratory_post_main','downstream_n':30,'counts':counts,'reference_families':2,'eligible_families':correction['eligible_counts_corrected'],'inaccessible_eligibility_unknown':3,'search_result_slots':320,'deduplicated_candidate_projects':148},indent=2))
 fields=['index','benchmark','canonical','revision','classification','source_granularity','output_target','transformation','limitations','verification','all_observed_units_retained','second_pass']
 with (A/'classification_ledger.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(ledger)
 refs=[{'benchmark':'QASPER','canonical':pins[107]['canonical'],'revision':pins[107]['revision'],'classification':'preserved','scope':'Official evaluator keeps references and takes best evidence F1. Official training labels may aggregate; reference classification is restricted to evaluator objective.','files':[x for x in fm if x['index']==107]}, {'benchmark':'SciFact','canonical':pins[124]['canonical'],'revision':pins[124]['revision'],'classification':'preserved','scope':'Official abstract-level criterion accepts a complete rationale; sentence scoring has its own coverage target. scifact-evaluator is grouped with official lineage.','files':[x for x in fm if x['index'] in [124,136]]}]
 refs[0]['official_dataset_distribution']={'canonical':pins[99]['canonical'],'revision':pins[99]['revision'],'classification':'preserved','fixture_index':99}
 refs[1]['official_dataset_distribution']={'canonical':pins[129]['canonical'],'revision':pins[129]['revision'],'classification':'preserved','fixture_index':129}
 (A/'reference_cases.json').write_text(json.dumps(refs,indent=2));print(json.dumps(counts));print('fixtures',len(fixture),'passed')
if __name__=='__main__':main()

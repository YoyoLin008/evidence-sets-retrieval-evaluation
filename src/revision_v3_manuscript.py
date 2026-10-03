"""Source-linked manuscript integration for revision-added exploratory results.

No partial encoder effectiveness is read. Final builds require the complete
encoder record and matching complete statistical outputs; an explicit draft
switch exists only for layout work before full inference finishes.
"""
from pathlib import Path
import hashlib
import json
import re
import pandas as pd

METHODS = {'bm25': 'BM25', 'tfidf': 'TF-IDF', 'dense': 'MiniLM', 'lead': 'Lead', 'random': 'Random', 'qwen3': 'Qwen3'}
CORPORA = {'qasper': 'QASPER', 'scifact': 'SciFact'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def one(frame, **where):
    for key, value in where.items():
        frame = frame[frame[key] == value]
    if len(frame) != 1:
        raise ValueError(f'Expected exactly one source row: {where}; found {len(frame)}')
    return frame.iloc[0]


def interval(row, key='mean', scale=100, digits=1):
    lo = 'lo' if key == 'mean' else key + '_lo'
    hi = 'hi' if key == 'mean' else key + '_hi'
    if pd.isna(row[key]):
        return 'Not attained'
    return f'{row[key]*scale:.{digits}f} [{row[lo]*scale:.{digits}f}, {row[hi]*scale:.{digits}f}]'


def source_denominators(root):
    path = root / 'revisions/v3/statistics/source_denominators.json'
    record = json.loads(path.read_text())
    freeze_path = root / 'logs/main_freeze.json'
    freeze = json.loads(freeze_path.read_text())
    if record['main_freeze_sha256'] != sha(freeze_path):
        raise ValueError('Source-denominator record has a different original freeze')
    for name, expected in record['input_sha256'].items():
        if freeze['input_files'][name] != expected:
            raise ValueError('Source-denominator hash disagrees with original input manifest')
        if (root / name).exists() and sha(root / name) != expected:
            raise ValueError(f'Present source input differs from frozen source: {name}')
    return record['values']


class Revision:
    def __init__(self, root, require_qwen=True):
        self.root = Path(root)
        self.statistics = self.root / 'revisions/v3/statistics'
        self.encoder = self.root / 'revisions/v3/encoder'
        self.pipeline_dir = self.root / 'revisions/v3/pipeline'
        self.examples_path = self.root / 'revisions/v3/examples/panels.json'
        self.dependencies = {}
        def read(relative):
            path = self.root / relative
            self.dependencies[relative] = sha(path)
            return json.loads(path.read_text())
        self.read = read
        self.validation = read('revisions/v3/statistics/validation.json')
        self.manifest = read('revisions/v3/statistics/manifest.json')
        if sha(self.root/'src/revision_v3_statistics.py') != self.manifest['source_sha256']:
            raise ValueError('Statistics source differs from its execution manifest; regenerate statistics')
        if self.dependencies['revisions/v3/statistics/validation.json'] != self.manifest['validation_sha256']:
            raise ValueError('Statistics validation does not match its manifest')
        if sha(self.root/'reference_outputs/main_v1/rankings.jsonl') != self.manifest['input_sha256']['original_rankings']:
            raise ValueError('Public saved rankings do not match statistics input hash')
        self.pipeline_manifest = read('revisions/v3/pipeline/manifest.json')
        if sha(self.root/'src/revision_v3_pipeline.py') != self.pipeline_manifest['source_code_sha256']:
            raise ValueError('Pipeline source differs from executed manifest')
        if sha(self.pipeline_dir/'plan.json') != self.pipeline_manifest['selection_plan_sha256']:
            raise ValueError('Pipeline selection plan differs from executed manifest')
        for name in ['report.json', 'main_cohort_alignment.json', 'score_summary.csv', 'paired_contrasts.csv']:
            if sha(self.pipeline_dir/name) != self.pipeline_manifest['outputs_sha256'][name]:
                raise ValueError(f'Pipeline output differs from executed manifest: {name}')
        self.pipeline = read('revisions/v3/pipeline/report.json')
        self.examples = read('revisions/v3/examples/panels.json')
        self.freeze = read('revisions/v3/encoder/runtime_freeze.json')
        self.technical = read('revisions/v3/encoder/public_technical_summary.json')['record']
        self.complete = (self.encoder / 'scoring_complete.json').exists()
        if require_qwen and not self.complete:
            raise ValueError('Final manuscript build requires complete Qwen scoring; use --draft-without-qwen only for internal layout work')
        if self.complete:
            self.scoring = read('revisions/v3/encoder/scoring_complete.json')
            self.inference = read('revisions/v3/encoder/inference_complete.json')
            self.encoder_validation = read('revisions/v3/encoder/validation.json')
            if self.scoring['rankings'] != 1084 or self.scoring['points'] != 6504 or not self.encoder_validation['passed']:
                raise ValueError('Encoder completion record is incomplete or unvalidated')
            actual = sha(self.encoder / 'rankings.jsonl')
            if actual != self.scoring['rankings_sha256'] or actual != self.manifest['input_sha256'].get('qwen_rankings'):
                raise ValueError('Statistics do not match the complete encoder rankings; rerun revision_v3_statistics.py --qwen')
            if self.validation['ranking_rows'] != 6504 or self.validation['scoring_points'] != 39024:
                raise ValueError('Combined complete-cohort method totals are inconsistent')
        elif 'qwen3' in self.validation['methods']:
            raise ValueError('Statistics expose Qwen outcomes without a validated complete encoder run')
        self.frames = {}
        for name in ['agreement_pruning', 'budget_thresholds', 'cost_distributions', 'costs', 'primary', 'method_contrasts']:
            relative = f'revisions/v3/statistics/{name}.csv'
            path = self.root / relative
            if sha(path) != self.manifest['outputs'][name + '.csv']:
                raise ValueError(f'Changed statistics table without matching manifest: {relative}')
            self.dependencies[relative] = sha(path)
            self.frames[name] = pd.read_csv(path)
        for name in ['score_summary', 'paired_contrasts']:
            path = self.pipeline_dir / (name + '.csv')
            self.dependencies[str(path.relative_to(self.root))] = sha(path)
            self.frames['pipeline_' + name] = pd.read_csv(path)
        self.table_sources = {}

    def table(self, doc, name, caption, headers, rows, widths, sources):
        doc['tables'][name] = dict(caption=caption, headers=headers, rows=[[str(x) for x in row] for row in rows], widths=widths)
        self.table_sources[name] = sources

    def populate(self, add):
        def put(name, text, sources):
            add(name, text, sources)
        stats = 'revisions/v3/statistics/'
        b = self.frames['budget_thresholds']
        q = one(b, dataset='qasper', method='bm25', budget_unit='units', tau=.75)
        s = one(b, dataset='scifact', method='bm25', budget_unit='units', tau=.75)
        put('BudgetResults', f'At 75% completion, BM25 requires {q.B_C:.0f} QASPER paragraphs under C and {q.B_A:.0f} under A: a uniform-budget difference of {interval(q, "difference", 1, 0)} paragraphs. SciFact requires {s.B_C:.0f} versus {s.B_A:.0f} sentences, a difference of {interval(s, "difference", 1, 0)}. The table retains all three prespecified thresholds; every point estimate and bootstrap threshold is attained.', stats+'budget_thresholds.csv')
        put('BudgetInterpretation', 'These exact minima invert the full empirical completion curves: every possible integer prefix depth is represented by its completion events. They describe one common budget for the population, whereas mean extra depth averages different item-specific stopping points. Short documents stay in the denominator after saturation. The supplementary lexical-token thresholds retain the same complete-prefix rule; neither statistic measures human reading time or deployed inference cost.', stats+'protocol.md; budget_thresholds.csv')
        shared_papers = self.validation['checks']['qasper']['answer_groups']['papers_shared_across_subsets']
        put('PruningDetails', f'The three rows use the original exact normalized-answer Boolean. Questions partition into agreement and its complement, but {shared_papers} papers appear in both; no independent-groups comparison is inferred. Each within-row pruning difference uses the same item rankings and paired paper-cluster draws. The four structure categories remain mutually exclusive and exhaustive; their counts below describe the original annotations. Pruning preserves C and dC but may change best-reference F1, as the counterexample in the main text shows.', stats+'validation.json; agreement_pruning.csv')
        put('BudgetDetails', 'Thresholds use 10,000 paired resamples of the original paper clusters or connected SciFact components, seed 20261002, with item-weighted denominators. C and A budgets and their difference are recalculated inside each draw. Percentile endpoints use linear interpolation and may be fractional for this discrete statistic. Unattained thresholds remain infinite and are counted rather than dropped; none occurred here. Positive-cost distributions condition on affected items and their represented clusters. All-method unit/token thresholds, quantiles, zero shares, and pointwise comparisons at all six original k values are retained in the machine-readable tables.', stats+'protocol.md; budget_thresholds.csv; cost_distributions.csv')
        put('AgreeExampleCandidates', self.examples['new_candidate_count'], 'revisions/v3/examples/panels.json')
        put('ExampleDetails', 'The new panel uses the first SHA-256-ranked eligible ID without substitution. All original outcomes were already visible, and C=1/A=0 was a selection criterion. The annotation answers agree exactly, but paragraph 20 describes the data while paragraph 24 describes a fluency criterion; the difference in directness is retained. This is an annotation-defined illustration, not a human-validated rate of semantic sufficiency. Source positions, unit hashes, selection candidates, brief excerpts, and original answer metadata are retained in the example ledger.', 'revisions/v3/examples/panels.json')
        report = self.pipeline
        mc, native = report['main_cohort'], report['native_dev']
        put('PipelineMethods', f'We selected the already-audited sscc-rag-paper converter and scorer under a written bounded rule. The pinned commit is {report["upstream"].rsplit("/",1)[-1][:12]}. Its unchanged native development loader exported {native["queries"]:,} queries; a data-supply wrapper reproduced that output exactly, then supplied the frozen test data to the same conversion logic. The actual JSONL export/reload and ir_measures scorer were executed. Scoring maps the original normalized body-text units to canonical exported IDs and reuses the five frozen rankings, rather than reproducing the upstream pooled retrieval or generator.', 'revisions/v3/pipeline/report.json')
        pp = self.frames['pipeline_score_summary']
        gap = one(pp, method='bm25', metric='complete_without_union')
        c, a, recall, ndcg = [one(pp, method='bm25', metric=m)['mean'] for m in ['complete','union_complete','R@5','nDCG@10']]
        put('PipelineResults', f'All {mc["original_n"]} eligible questions were exported. Under the explicit normalized-text mapping and candidate restriction, {mc["scored_n"]} questions in {mc["scored_papers"]} papers have exact source-union/export-membership equality; {mc["excluded_n"]} fail because strip-only matching loses evidence. At k=5 on the aligned subset, BM25 gives C={100*c:.1f}%, A={100*a:.1f}%, and a gap of {interval(gap)} points. Actual Recall@5 is {100*recall:.1f}% and nDCG@10 is {100*ndcg:.1f}%; Recall@5 equals union overlap recall, and Success@5 equals H. Neither is union completion.', 'revisions/v3/pipeline/report.json; score_summary.csv')
        pc = self.frames['pipeline_paired_contrasts']
        c_diff, a_diff = [one(pc, contrast='MiniLM minus BM25', metric=m)['mean'] for m in ['complete','union_complete']]
        put('PipelineInterpretation', f'MiniLM’s completion advantage over BM25 is {100*c_diff:.2f} points under C and {100*a_diff:.2f} under A on this subset. The best-reference and union-F1 method orderings remain stable. The upstream scorer explicitly evaluates conventional relevance objectives; no mismatch between its stated objective and implementation is established. The case demonstrates lost information for recovering C and sensitivity of an added completion comparison, within a controlled candidate restriction. It does not show that ordinary relevance metrics should be replaced by A or C.', 'revisions/v3/pipeline/report.json; paired_contrasts.csv')
        alignment = self.read('revisions/v3/pipeline/main_cohort_alignment.json')
        exact = [r for r in alignment if r['membership_category'] == 'exact_union_membership']
        ambiguous = sum(bool(r['normalized_text_ambiguities']) for r in exact)
        assert ambiguous == mc['exact_membership_any_text_ambiguity_questions']
        put('PipelineSupplement', f'The test export contains {report["test_export"]["queries"]:,} queries and {report["test_export"]["corpus_units"]:,} paragraph IDs from {report["test_export"]["raw_questions"]:,} source questions. The raw flow differs from the strict main-cohort intersection. The aligned {mc["scored_n"]}-question subset includes {mc["exact_union_multiset_questions"]} items with multiple distinct source sets and {mc["exact_union_one_distinct_set_questions"]} with one set. {ambiguous} aligned questions have multiple export candidates sharing normalized text ({mc["exact_membership_gold_text_ambiguity_questions"]} involving gold); {mc["exact_membership_abstract_id_mapping_questions"]} have a body unit mapped to an identical normalized abstract candidate ({mc["exact_membership_abstract_gold_id_mapping_questions"]} involving gold). IDs follow the first normalized-text match. The ledger retains these ambiguities; original body-text units and ranking order remain fixed, while abstract-only text and other papers are excluded. Thus exact membership equality is conditional on the stated text mapping; it is not an assertion that the entire native task underwent pure grouping loss. Every original item has a candidate-scope change relative to the upstream pooled task. The {mc["excluded_n"]} membership failures and all IDs remain visible. Direct formulas match the actual scorer within {report["validation"]["real_scorer_formula_max_absolute_error"]:.2g}. The historical MTEB count 576/1,335 is not used as this intersection’s denominator.', 'revisions/v3/pipeline/report.json; main_cohort_alignment.json')
        config = self.freeze['config']
        put('QwenMethods', f'The revision adds Qwen3-Embedding-0.6B [[qwen]]. Its fixed revision is {config["revision"][:12]}, selected before its effectiveness was observed. It uses {config["dtype"]} {config["device"].upper()} inference, {config["pooling"].replace("_"," ")} pooling with attention masks, {config["padding_side"]} padding, L2 normalization, {config["dimensions"]:,} dimensions, and an {config["max_length"]:,}-model-token limit. Queries receive one fixed scientific-evidence instruction; documents do not. Original candidates, index-based tie breaking, budgets, and cluster labels are retained.', 'revisions/v3/encoder/runtime_freeze.json')
        put('RevisionTiming', 'The new subgroup/pruning, uniform-budget, converter/scorer, example, and full-encoder plans were recorded after the v1.0.0 findings were known. They are revision-added exploratory work, not an extension of the original preregistration. The historical joint sensitivity and two-hour timing decision remain archived; the new complete encoder run uses a separately frozen configuration and cache.', 'revisions/v3/plan.md; statistics/protocol.md; encoder/runtime_freeze.json')
        if not self.complete:
            for key in ['QwenResults','QwenComparisons','QwenLimitations','QwenTechnicalDetails']:
                put(key, 'INTERNAL LAYOUT DRAFT: complete Qwen inference and validation are pending; no partial effectiveness results are included.', 'revisions/v3/encoder/runtime_freeze.json')
        else:
            p, costs = self.frames['primary'], self.frames['costs']
            pieces = []
            for dataset in ['qasper','scifact']:
                h, c, a = [one(p,dataset=dataset,method='qwen3',metric=m)['mean'] for m in ['hit','complete','union_complete']]
                gap = one(p,dataset=dataset,method='qwen3',metric='complete_without_union')
                cost = one(costs,dataset=dataset,method='qwen3',metric='depth_penalty')
                pieces.append(f'{CORPORA[dataset]} H/C/A={100*h:.1f}/{100*c:.1f}/{100*a:.1f}%, C−A={interval(gap)} points, and mean extra depth {cost["mean"]:.2f} (median {cost["median"]:.0f})')
            put('QwenResults', 'Complete Qwen3 rankings yield '+ '; '.join(pieces)+f'. The revision contains {self.validation["ranking_rows"]:,} full rankings and {self.validation["scoring_points"]:,} points across the six original unit budgets when the historical and new methods are counted together; the original block remains unchanged.', stats+'primary.csv; costs.csv; validation.json')
            contrast = self.frames['method_contrasts']
            sentences=[]
            for dataset in ['qasper','scifact']:
                c = one(contrast,dataset=dataset,method_left='qwen3',method_right='bm25',primary=True,metric='complete')
                a = one(contrast,dataset=dataset,method_left='qwen3',method_right='bm25',primary=True,metric='union_complete')
                sentences.append(f'{CORPORA[dataset]} Qwen3−BM25 differences are {100*c.mean_difference:.1f} points under C and {100*a.mean_difference:.1f} under A')
            reversed_pairs=[]
            for dataset in ['qasper','scifact']:
                for right in ['bm25','dense']:
                    f = one(contrast,dataset=dataset,method_left='qwen3',method_right=right,primary=True,metric='max_f1').mean_difference
                    u = one(contrast,dataset=dataset,method_left='qwen3',method_right=right,primary=True,metric='union_f1').mean_difference
                    if f*u<0: reversed_pairs.append(f'{CORPORA[dataset]} Qwen3 versus {METHODS[right]}')
            f1text = ('The fixed revision-added exploratory comparisons show no new primary F1 ranking reversal.' if not reversed_pairs else 'A point-estimate F1 ordering change occurs for '+', '.join(reversed_pairs)+'; pointwise intervals do not establish a multiplicity-controlled reversal.')
            put('QwenComparisons', '; '.join(sentences)+'. '+f1text+' The supplement reports every primary paired comparison against BM25 and MiniLM; all six budgets and all fixed metrics remain in the machine-readable results. These are exploratory pointwise comparisons.', stats+'method_contrasts.csv')
            trunc = [json.loads(line) for line in (self.encoder/'truncation.jsonl').read_text().splitlines()]
            if len(trunc) != 1084 or sha(self.encoder/'truncation.jsonl') != self.scoring['truncation_sha256']:
                raise ValueError('Truncation audit does not match complete scoring')
            query_trunc=sum(r['query_truncated'] for r in trunc)
            any_trunc=sum(bool(r['truncated_units']) for r in trunc)
            gold_trunc=sum(r['any_gold_truncated'] for r in trunc)
            put('QwenLimitations', f'The single modern encoder is a robustness check, not a model survey or deployment evaluation. Its full audit records {query_trunc} truncated queries, {any_trunc} items with truncated candidates, and {gold_trunc} with truncated annotated evidence. Its tokenizer counts differ from the lexical cost measure. Qwen’s 8,192-token allowance and MiniLM’s 256-wordpiece allowance differ: with candidates and evaluation fixed, any performance advantage cannot be attributed to architecture alone.', 'revisions/v3/encoder/truncation.jsonl')
            self.dependencies['revisions/v3/encoder/truncation.jsonl']=sha(self.encoder/'truncation.jsonl')
            cpu=self.technical['backends']['cpu']
            put('QwenTechnicalDetails', f'The completed run encoded {self.inference["total"]:,} distinct instructed-query/document inputs with CPU float32, batch size at most {config["batch_size"]}, at most {config["max_padded_tokens"]:,} padded batch tokens (longer inputs singly), and {config["threads"]} CPU threads. Full inference session time was {self.inference["seconds"]/3600:.2f} hours. The technical-only MPS trial failed the valid-vector check, so it was not used for effectiveness. CPU single-versus-batch maximum coordinate difference was {cpu["batch_comparison"]["max_coordinate_difference"]:.2g}, and repeated encoding was exact. The {config["max_length"]:,}-token limit truncated {self.inference["unique_truncated"]} unique inputs; maximum observed length was {self.inference["max_model_tokens"]:,} model tokens. Query instruction: “{config["query_instruction"]}.” Model, tokenizer, dependencies, input roles, pooling, precision, and source fingerprints are bound in the cache key. All {self.scoring["rankings"]:,} rankings are complete original-candidate permutations; the encoder audit and separate statistics replay validate them.', 'revisions/v3/encoder/runtime_freeze.json; public_technical_summary.json; inference_complete.json; scoring_complete.json')
        put('RevisionConclusion', 'The executed converter/scorer path shows that a legitimate flat relevance export can lose information needed for an added completion target, without establishing a fault in its stated relevance evaluation. Uniform completion thresholds translate that distinction into explicit annotation-defined population budgets; the full-encoder check tests its persistence under one additional ranking model.', 'revisions/v3/pipeline/report.json; statistics/budget_thresholds.csv; encoder/scoring_complete.json')

    def enrich(self, doc):
        tables = doc['tables']
        f = self.frames['agreement_pruning']
        labels = [('exact_answer_agreement','Exact agreement'),('agreement_complement','Complement'),('full','Full cohort')]
        rows=[]; topology=[]
        for key,label in labels:
            r=one(f,method='bm25',group=key)
            rows.append([label,f'{int(r.n)}/{int(r.papers)}',interval(r,'original_gap'),interval(r,'pruned_gap'),interval(r,'pruned_minus_original')])
            topology.append([label,str(int(r.n))]+[str(int(r[f'topology_{i}_n'])) for i in range(4)])
        self.table(doc,'pruning_v3','Revision-added exploratory QASPER BM25 at k=5. n/p gives questions/papers; papers overlap across subsets. Gap values are percentage points with paired paper-cluster 95% intervals. The last column is a within-item target transformation, not a causal comparison between cohorts.',['Cohort','n/p','Original C−A','Pruned C−A','Pruned − original'],rows,[69,50,105,104,104],['revisions/v3/statistics/agreement_pruning.csv'])
        self.table(doc,'pruning_topology_v3','Original topology within the QASPER answer subgroups. Categories: one distinct set; multiple sets with one minimal set; multiple minimal sets without supersets; multiple minimal sets plus supersets. Subgroups partition questions, not papers.',['Cohort','n','One set','One minimal','Multi minimal; no supersets','Multi minimal + supersets'],topology,[86,36,58,68,92,92],['revisions/v3/statistics/agreement_pruning.csv'])
        b=self.frames['budget_thresholds']
        for unit,name in [('units','budgets_v3'),('lexical_tokens','budgets_tokens_v3')]:
            rows=[]
            for dataset in ['qasper','scifact']:
                for tau in [.5,.75,.9]:
                    r=one(b,dataset=dataset,method='bm25',budget_unit=unit,tau=tau)
                    rows.append([f'{CORPORA[dataset]} / {tau:.0%}',interval(r,'B_C',1,0),interval(r,'B_A',1,0),interval(r,'difference',1,0)])
            caption=('Units are paragraphs for QASPER and sentences for SciFact.' if unit=='units' else 'Lexical-token budgets admit complete prefixes without skipping or truncating the next unit.')
            self.table(doc,name,'Revision-added exploratory BM25 minimum uniform budgets, with paired 95% cluster intervals. '+caption+' All three thresholds use every eligible item; all bootstrap thresholds are attained. These are population thresholds, not mean individual extra costs.',['Corpus / target','B_C [CI]','B_A [CI]','B_A−B_C [CI]'],rows,[96,108,108,120],['revisions/v3/statistics/budget_thresholds.csv'])
        dist=self.frames['cost_distributions'];rows=[]
        for dataset in ['qasper','scifact']:
            for metric,label in [('depth_penalty','units'),('tokens_penalty','tokens')]:
                a=one(dist,dataset=dataset,method='bm25',metric=metric,subset='all')
                p=one(dist,dataset=dataset,method='bm25',metric=metric,subset='positive_cost')
                rows.append([f'{CORPORA[dataset]} / {label}',f'{int(p.n)}/{int(p.clusters)}',f'{100*a.overall_zero_fraction:.1f}',interval(a,scale=1,digits=1),interval(p,scale=1,digits=1),f'{p["median"]:.0f} / {p.q90:.1f}'])
        self.table(doc,'affected_v3','Revision-added exploratory BM25 cost distributions. Positive n/g gives affected items/represented clusters; zero shares use the full 875/209-item populations. Conditional mean intervals resample represented clusters among affected items. Full distributions and every method remain in the machine-readable tables.',['Corpus / cost','Positive n/g','Zero (%)','All mean [CI]','Positive mean [CI]','Positive median / q90'],rows,[70,54,43,90,95,80],['revisions/v3/statistics/cost_distributions.csv'])
        pp=self.frames['pipeline_score_summary'];rows=[]
        for method in ['bm25','tfidf','dense','lead','random']:
            rows.append([METHODS[method]]+[f'{one(pp,method=method,metric=m)["mean"]*100:.1f}' for m in ['R@5','nDCG@10','complete','union_complete']]+[interval(one(pp,method=method,metric='complete_without_union'))])
        self.table(doc,'pipeline_v3',f'Revision-added real converter/scorer replay on {self.pipeline["main_cohort"]["scored_n"]} questions in {self.pipeline["main_cohort"]["scored_papers"]} papers, with exact union membership under the stated text mapping and original candidate restriction. Actual Recall/nDCG are conventional relevance measures; C/A are separate completion targets at k=5. The paired gap uses paper-cluster 95% intervals. This is not native pooled-retrieval performance.',['Method','Recall@5 (%)','nDCG@10 (%)','C (%)','A (%)','C−A, pp [CI]'],rows,[52,61,76,51,51,141],['revisions/v3/pipeline/score_summary.csv','revisions/v3/pipeline/report.json'])
        for panel in self.examples['panels']:
            name = 'case_agreement_v3' if panel['role'].startswith('new ') else 'case_'+panel['dataset']
            family='; '.join('E'+str(i+1)+'={'+','.join(map(str,g))+'}' for i,g in enumerate(panel['gold']))
            excerpts='; '.join(f'{u["index"]}: “{u["short_verbatim_excerpt"]}”' for u in panel['units'] if 'short_verbatim_excerpt' in u)
            answer='; '.join(panel.get('answer_display',[])) if panel['dataset']=='qasper' else panel['label']
            source=f'{panel["paper_or_document_id"]}; item {panel["id"]}'
            scores=panel['scores'];cost=panel['costs']
            rows=[['Source IDs',source],['Question / claim',panel['query']],['Answer / label',answer],['Evidence family',family],['Exact prefix','['+','.join(map(str,panel['ranking_prefix']))+f'] at k={panel["k"]}'],['Completion',f'H={scores["hit"]}, C={scores["complete"]}, A={scores["union_complete"]}; dC={cost["depth_complete"]}, dA={cost["depth_union"]}'],['Brief unit excerpts',excerpts],['Interpretation',panel['interpretation']]]
            self.table(doc,name,'Exploratory annotation case: '+CORPORA[panel['dataset']]+'. Unit indices are zero-based in the released mapping; source-unit IDs use paper:paragraph:index or abstract:sentence:index. Brief excerpts are from the identified source. No new human semantic validation is claimed.',['Field','Recorded example'],rows,[91,341],['revisions/v3/examples/panels.json'])
        if self.complete:
            p=self.frames['primary'];cost=self.frames['costs']
            for dataset,primary in [('qasper',5),('scifact',3)]:
                tables['primary']['rows'].append([f'{CORPORA[dataset]} / {primary}','Qwen3']+[f'{one(p,dataset=dataset,method="qwen3",metric=m)["mean"]*100:.1f}' for m in ['hit','complete','union_complete']]+[interval(one(p,dataset=dataset,method='qwen3',metric='complete_without_union'))])
                a=one(cost,dataset=dataset,method='qwen3',metric='depth_penalty');t=one(cost,dataset=dataset,method='qwen3',metric='tokens_penalty')
                tables['costs']['rows'].append([CORPORA[dataset],'Qwen3',interval(a,scale=1,digits=2),f'{a["median"]:.0f} [{a.q25:.0f}, {a.q75:.0f}]',interval(t,scale=1,digits=1)])
            tables['primary']['rows'].sort(key=lambda row: 0 if row[0].lower().startswith('qasper') else 1)
            tables['costs']['rows'].sort(key=lambda row: 0 if row[0].lower().startswith('qasper') else 1)
            tables['primary']['caption']+=' Qwen3 is revision-added exploratory; other rows are the frozen original analysis.'
            tables['costs']['caption']+=' Qwen3 is revision-added exploratory.'
            rows=[];contra=self.frames['method_contrasts']
            for dataset in ['qasper','scifact']:
                for right in ['bm25','dense']:
                    cells=[]
                    for metric in ['complete','union_complete','max_f1','union_f1']:
                        r=one(contra,dataset=dataset,method_left='qwen3',method_right=right,primary=True,metric=metric)
                        cells.append(interval(r.rename({'mean_difference':'mean'})))
                    rows.append([f'{CORPORA[dataset]}: Qwen3−{METHODS[right]}']+cells)
            self.table(doc,'qwen_contrasts_v3','Revision-added exploratory Qwen3 differences at primary budgets. All values are percentage points, including F1×100, with paired pointwise 95% cluster intervals. These four fixed comparisons are retained regardless of sign; no multiplicity-controlled significance claim is made.',['Corpus / contrast','C [CI]','A [CI]','Best-ref F1 [CI]','Union F1 [CI]'],rows,[96,84,84,84,84],['revisions/v3/statistics/method_contrasts.csv'])
        else:
            self.table(doc,'qwen_contrasts_v3','Internal layout draft; no partial effectiveness results.',['Status'],[['Full Qwen results pending']],[432],['revisions/v3/encoder/runtime_freeze.json'])
        doc['analysis_status']='Original frozen results; earlier post-main additions; revision-added exploratory results' if self.complete else 'INTERNAL LAYOUT DRAFT: incomplete encoder'
        return doc

    def abstract(self, values):
        b=self.frames['budget_thresholds'];q=one(b,dataset='qasper',method='bm25',budget_unit='units',tau=.75);s=one(b,dataset='scifact',method='bm25',budget_unit='units',tau=.75)
        result=(f'Scientific evidence annotations often group jointly required units and alternative sets. We quantify the consequences of choosing completion of one observed set (C) or the annotated union (A), holding candidates and rankings fixed for {values["Qn"]} QASPER questions and {values["Sn"]} SciFact claim–abstract pairs. At prespecified BM25 budgets, C/A are {values["QC"]}/{values["QA"]}% and {values["SC"]}/{values["SA"]}%, respectively; paired gaps are {values["QCA"]} and {values["SCA"]} percentage points. Mean extra union-completion depth is {values["QDepth"]} paragraphs and {values["SDepth"]} sentences, with zero medians and no original primary F1 ranking reversal. Revision-added exploratory analysis shows that 75% completion needs uniform BM25 budgets of {q.B_C:.0f} versus {q.B_A:.0f} paragraphs and {s.B_C:.0f} versus {s.B_A:.0f} sentences. A real converter/scorer replay aligns {self.pipeline["main_cohort"]["scored_n"]} QASPER questions under an explicit candidate restriction: the flat export cannot generally recover C, while its conventional relevance metrics remain appropriate to their stated objective. ')
        if self.complete:
            p=self.frames['primary'];gaps=[one(p,dataset=d,method='qwen3',metric='complete_without_union')['mean']*100 for d in ['qasper','scifact']]
            result+=f'Complete Qwen3-Embedding-0.6B rankings yield gaps of {gaps[0]:.1f} and {gaps[1]:.1f} points. '
        result+=f'Among {values["QagreeN"]} exact-answer-agreement questions, pruning yields an {values["QJointGap"]}-point gap, characterizing a restricted cohort and target rather than a bound or causal decomposition. The contribution is an empirical audit of annotation-defined measurement and budget sensitivity, not a new completion criterion or evidence of semantic sufficiency.'
        return result

    def supplement_abstract(self):
        return ('Supplementary evidence for the controlled evaluation audit: prior post-main topology and implementation records, and revision-added subgroup/pruning estimates, uniform-budget thresholds, complete Qwen3 results, executed converter/scorer outputs, and source-linked examples. Original and revision-added analyses retain separate provenance.' if self.complete else 'INTERNAL LAYOUT DRAFT: supplementary structure before the complete encoder results; no partial effectiveness is reported.')

    def save_provenance(self):
        path=self.statistics/'manuscript_integration.json'
        path.write_text(json.dumps({'status':'complete integration' if self.complete else 'internal layout draft', 'dependencies_sha256':self.dependencies,'tables':self.table_sources,'encoder_effectiveness_gate':'complete validated 1084-row run only; no partial outcomes'},indent=2)+'\n')

"""Guard source-linked manuscript assembly and incomplete-encoder disclosure."""
from pathlib import Path
import copy
import json
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from revision_v3_manuscript import Revision, source_denominators, interval

ROOT=Path(__file__).resolve().parents[1]


def test_source_denominators_require_matching_original_manifest(tmp_path):
    source=ROOT/'revisions/v3/statistics/source_denominators.json'
    if not source.exists():pytest.skip('Revision artifacts not available')
    for relative in ['revisions/v3/statistics/source_denominators.json','logs/main_freeze.json']:
        p=tmp_path/relative;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes((ROOT/relative).read_bytes())
    assert source_denominators(tmp_path)=={'Qpapers':416,'Qtotal':1451,'Sclaims':300,'Sevidenceclaims':188,'Snoevidence':112}
    metadata=json.loads((tmp_path/'logs/main_freeze.json').read_text())
    metadata['input_files']['data/raw/qasper-test-and-evaluator-v0/qasper-test-v0.3.json']='changed'
    (tmp_path/'logs/main_freeze.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError,match='different original freeze'):
        source_denominators(tmp_path)


def test_final_gate_draft_table_sources_and_protected_content():
    if not (ROOT/'revisions/v3/statistics/manifest.json').exists():pytest.skip('Revision outputs not available')
    revision=Revision(ROOT,require_qwen=False)
    if not revision.complete:
        with pytest.raises(ValueError,match='Final manuscript build requires'):
            Revision(ROOT)
    registry={}
    revision.populate(lambda k,v,s:registry.update({k:(str(v),s)}))
    assert '119 papers' in registry['PruningDetails'][0]
    assert registry['AgreeExampleCandidates'][0]=='16'
    assert 'partial effectiveness' not in registry['PipelineResults'][0]
    protected=[['p','Immutable author responsibility and AI disclosure.']]
    doc={'blocks':copy.deepcopy(protected),'tables':{'primary':{'rows':[],'caption':''},'costs':{'rows':[],'caption':''}}}
    revised=revision.enrich(doc)
    assert revised['blocks']==protected
    assert revised['tables']['pruning_v3']['rows'][0][1]=='195/149'
    assert revised['tables']['budgets_v3']['rows'][1][1].startswith('14 ')
    assert '866 questions' in revised['tables']['pipeline_v3']['caption']
    assert 'grammatical English' in str(revised['tables']['case_agreement_v3']['rows'])
    assert 'not an assertion' in registry['PipelineSupplement'][0]
    assert all(sum(t['widths'])==432 for t in revised['tables'].values() if 'widths' in t)

"""Create publication-safe technical evidence derived from preserved encoder records.

The immutable raw technical evidence remains local. This helper preserves every
measurement and sample identifier while replacing local diagnostic path prefixes.
It never computes retrieval effectiveness or changes the encoder freeze.
"""
from pathlib import Path
import datetime, hashlib, json, re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'revisions/v3/encoder'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(value):
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if isinstance(value, str):
        value = value.replace(str(ROOT), '<PROJECT_ROOT>')
        return re.sub(r'/Users/[^/]+/', '<HOME>/', value)
    return value


def main():
    original = OUT / 'technical_results.json'
    freeze = json.loads((OUT / 'runtime_freeze.json').read_text())
    if sha(original) != freeze['config']['technical_results_sha256']:
        raise ValueError('Original technical evidence does not match the freeze')
    summary = {'derived_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'source_file': 'technical_results.json', 'source_sha256': sha(original),
               'freeze_sha256': sha(OUT / 'runtime_freeze.json'),
               'transformation': 'All fields retained; only absolute local diagnostic path prefixes normalized. No numeric or sample evidence altered.',
               'record': normalize(json.loads(original.read_text()))}
    (OUT / 'public_technical_summary.json').write_text(json.dumps(summary, sort_keys=True, indent=2) + '\n')
    if not (OUT / 'validation.json').exists():
        return
    validation = json.loads((OUT / 'validation.json').read_text())
    if validation.get('passed') is not True or validation['rankings'] != 1084:
        raise ValueError('Complete full-cohort validation is required for the final report')
    sessions = [json.loads(s) for s in (OUT / 'inference_sessions.jsonl').read_text().splitlines()]
    complete = json.loads((OUT / 'inference_complete.json').read_text())
    status = json.loads((OUT / 'inference_status.json').read_text())
    inputs = json.loads((OUT / 'input_manifest.json').read_text())
    report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'role': 'revision-added exploratory complete-cohort robustness',
              'model': freeze['config']['model'], 'revision': freeze['config']['revision'],
              'backend': freeze['config']['device'], 'dtype': freeze['config']['dtype'],
              'unique_inputs': complete['total'], 'rankings': validation['rankings'],
              'unique_inputs_by_role': {role: sum(role in r for r in inputs['roles'].values()) for role in ['query', 'document']},
              'input_occurrences_by_role': {role: sum(r.get(role, 0) for r in inputs['roles'].values()) for role in ['query', 'document']},
              'original_unit_budget_scoring_points': validation['scoring_points'],
              'max_model_tokens': complete['max_model_tokens'], 'truncated_unique_inputs': complete['unique_truncated'],
              'inference_session_seconds': sum(x.get('seconds', 0) for x in sessions if x['event'] in ['failed', 'complete']),
              'runtime_scope': 'Sum of inference sessions including model load and cache writes, excluding prior technical sample, subsequent fingerprint scan/scoring/statistics.',
              'peak_process_rss_bytes': status['peak_process_rss_bytes'],
              'failed_inference_sessions': sum(x['event'] == 'failed' for x in sessions),
              'technical_mps_failed': not summary['record']['backends'].get('mps', {}).get('passes', False),
              'primary_frozen_rankings_modified': False,
              'scientific_statistics': 'See revision-v3 statistics outputs; this technical report does not select or summarize effectiveness.',
              'file_sha256': {name: sha(OUT / name) for name in ['rankings.jsonl', 'truncation.jsonl', 'embedding_manifest.json',
                             'input_manifest.json', 'runtime_freeze.json', 'validation.json', 'scoring_complete.json',
                             'inference_complete.json', 'public_technical_summary.json']}}
    (OUT / 'completion_report.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

"""Revision-added Qwen inference: technical sample, immutable freeze, resumable full run.

Commands (use the locked revision Python environment):
  python src/revision_v3_encoder.py technical
  python src/revision_v3_encoder.py infer
  python src/revision_v3_encoder.py score
  python src/revision_v3_encoder.py validate
No effectiveness is computed by technical/infer. Source inputs are never modified.
"""
from pathlib import Path
import argparse, collections, datetime, hashlib, importlib.metadata, json, os
import platform, resource, subprocess, sys, time, traceback
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'revisions/v3/encoder'
MODEL = ROOT / 'revisions/v2/compute/model'
INPUT = ROOT / 'outputs/main_v1/instances.jsonl'
REVISION = '97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3'
INSTRUCTION = 'Given a scientific question or claim, retrieve passages that provide evidence relevant to it'
SEED = 20261003


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return sha_bytes(json.dumps(value, sort_keys=True, ensure_ascii=False).encode())


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    tmp.replace(path)


def append(path, value):
    with Path(path).open('a') as f:
        f.write(json.dumps(value, sort_keys=True) + '\n')
        f.flush()
        os.fsync(f.fileno())


def query_text(text):
    return f'Instruct: {INSTRUCTION}\nQuery:{text}'


def text_hash(text):
    return sha_bytes(text.encode())


def collect_inputs(instances):
    texts, roles = {}, collections.defaultdict(collections.Counter)
    for x in instances:
        for role, values in [('query', [query_text(x['query'])]), ('document', x['units'])]:
            for text in values:
                h = text_hash(text)
                if h in texts and texts[h] != text:
                    raise ValueError('Unexpected SHA-256 collision')
                texts[h] = text
                roles[h][role] += 1
    return texts, {h: dict(r) for h, r in roles.items()}


def last_token_pool(hidden, mask):
    """Last non-padding position, valid for left, right and mixed-side fixtures."""
    import torch
    if mask.ndim != 2 or hidden.shape[:2] != mask.shape or (mask.sum(1) == 0).any():
        raise ValueError('Invalid attention mask')
    positions = torch.arange(mask.shape[1], device=mask.device).expand_as(mask)
    last = positions.masked_fill(mask == 0, -1).max(dim=1).values
    return hidden[torch.arange(hidden.shape[0], device=hidden.device), last]


def batches(keys, lengths, batch_size=4, max_padded_tokens=4096):
    """Stable increasing-length batches, except longer inputs remain singletons."""
    batch = []
    for h in sorted(keys, key=lambda h: (lengths[h], h)):
        if batch and (len(batch) >= batch_size or (len(batch) + 1) * min(lengths[h], 8192) > max_padded_tokens):
            yield batch
            batch = []
        batch.append(h)
    if batch:
        yield batch


def stable_order(scores):
    if not np.isfinite(scores).all():
        raise ValueError('Non-finite similarity')
    return sorted(range(len(scores)), key=lambda i: (-float(scores[i]), i))


def check_vectors(vectors, n):
    if vectors.shape != (n, 1024) or not np.isfinite(vectors).all():
        raise ValueError('Invalid embedding shape or values')
    if not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5, rtol=0):
        raise ValueError('Embedding is not normalized')


def comparison(a, b):
    diff = float(np.max(np.abs(a - b)))
    cos = float(np.min(np.sum(a.astype(np.float64) * b, axis=1)))
    return {'max_coordinate_difference': diff, 'minimum_cosine': cos,
            'passes': bool(diff <= 5e-4 and cos >= .9999)}


def setup():
    import torch
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(SEED)
    torch.use_deterministic_algorithms(True)
    return torch


def model_manifest():
    expected = json.loads((ROOT / 'revisions/v2/compute/model_manifest.json').read_text())
    actual = {name: sha_file(MODEL / name) for name in expected}
    if actual != expected:
        raise ValueError('Pinned model or tokenizer differs from acquired v2 files')
    metadata = json.loads((OUT / 'official_revision.json').read_text())
    if metadata['sha'] != REVISION:
        raise ValueError('Official model revision mismatch')
    return actual


def dependencies():
    return {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}


def instantiate(device):
    import torch
    from transformers import AutoModel, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, padding_side='left')
    model = AutoModel.from_pretrained(MODEL, local_files_only=True, torch_dtype=torch.float32,
                                      attn_implementation='sdpa').to(device).eval()
    return model, tok


def synchronize(device):
    if device == 'mps':
        import torch
        torch.mps.synchronize()


def encode(model, tok, texts, device):
    import torch
    inputs = tok(texts, padding=True, truncation=True, max_length=8192, return_tensors='pt').to(device)
    with torch.inference_mode():
        hidden = model(**inputs, use_cache=False).last_hidden_state
        vectors = torch.nn.functional.normalize(last_token_pool(hidden, inputs['attention_mask']), p=2, dim=1)
    synchronize(device)
    arr = vectors.cpu().numpy().astype(np.float32)
    check_vectors(arr, len(texts))
    return arr


def load_inputs():
    xs = [json.loads(s) for s in INPUT.read_text().splitlines()]
    counts = dict(collections.Counter(x['dataset'] for x in xs))
    if counts != {'qasper': 875, 'scifact': 209}:
        raise ValueError(f'Unexpected original cohorts: {counts}')
    return xs


def technical():
    if (OUT / 'runtime_freeze.json').exists():
        raise ValueError('Freeze already exists; use infer/score/validate, do not overwrite it')
    torch = setup()
    from transformers import AutoTokenizer
    manifest = model_manifest()
    texts, roles = collect_inputs(load_inputs())
    tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, padding_side='left')
    lengths = {h: len(tok(t, truncation=False)['input_ids']) for h, t in texts.items()}
    bins = np.array_split(sorted(texts, key=lambda h: (lengths[h], h)), 4)
    sample = []
    for b, keys in enumerate(bins):
        chosen = sorted(keys)[:4]
        longest = max(keys, key=lambda h: (lengths[h], h))
        if longest not in chosen:
            chosen.append(longest)
        sample.extend({'bin': b, 'hash': str(h), 'length': lengths[h]} for h in chosen)
    write_json(OUT / 'input_manifest.json', {'unique_inputs': len(texts), 'input_sha256': sha_file(INPUT),
               'lengths': lengths, 'roles': roles, 'sample': sample, 'max_model_tokens': max(lengths.values()),
               'truncated_unique_inputs': sum(v > 8192 for v in lengths.values()),
               'selection': 'First 4 SHA256 keys and longest input in each equal-count length quartile'})
    print('Technical sample:', len(sample), 'of', len(texts), 'inputs; no retrieval effectiveness', flush=True)
    results = {'utc': now(), 'prior_results_known': True, 'effectiveness_computed': False,
               'platform': platform.platform(), 'cpu_threads': 2, 'mps_available': torch.backends.mps.is_available(),
               'sample': sample, 'backends': {}}
    vectors_by_device = {}
    for device in ['cpu'] + (['mps'] if torch.backends.mps.is_available() else []):
        try:
            start = time.perf_counter()
            model, tok = instantiate(device)
            load_time = time.perf_counter() - start
            keys = [r['hash'] for r in sample]
            encode(model, tok, [texts[min(texts, key=lambda h: (lengths[h], h))]], device)
            singles, timings = {}, []
            for r in sample:
                t = time.perf_counter()
                singles[r['hash']] = encode(model, tok, [texts[r['hash']]], device)[0]
                timings.append({**r, 'seconds': time.perf_counter() - t})
            batched = {}
            t = time.perf_counter()
            for batch in batches(keys, lengths):
                arr = encode(model, tok, [texts[h] for h in batch], device)
                batched.update(zip(batch, arr))
            batch_seconds = time.perf_counter() - t
            ordered = np.stack([singles[h] for h in keys])
            batch_arr = np.stack([batched[h] for h in keys])
            repeat = encode(model, tok, [texts[keys[0]]], device)
            rep = comparison(ordered[:1], repeat)
            batching = comparison(ordered, batch_arr)
            result = {'load_seconds': load_time, 'single_seconds': sum(r['seconds'] for r in timings),
                      'batched_seconds': batch_seconds, 'singleton_timings': timings,
                      'batch_comparison': batching, 'repeat_comparison': rep,
                      'peak_process_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
            if device == 'mps':
                result['cpu_comparison'] = comparison(vectors_by_device['cpu'], ordered)
                result['allocated_mps_bytes'] = torch.mps.current_allocated_memory()
                result['driver_mps_bytes'] = torch.mps.driver_allocated_memory()
            result['passes'] = batching['passes'] and rep['passes'] and result.get('cpu_comparison', {'passes': True})['passes']
            vectors_by_device[device] = ordered
            results['backends'][device] = result
            del model
            if device == 'mps':
                torch.mps.empty_cache()
        except Exception as exc:
            results['backends'][device] = {'passes': False, 'error': repr(exc), 'traceback': traceback.format_exc()}
            append(OUT / 'failures.jsonl', {'utc': now(), 'phase': 'technical', 'device': device, 'error': repr(exc)})
        write_json(OUT / 'technical_results.json', results)
        print(device, results['backends'][device], flush=True)
    cpu = results['backends']['cpu']
    if not cpu['passes']:
        raise ValueError('CPU reference failed; inspect technical results')
    mps = results['backends'].get('mps', {})
    device = 'mps' if mps.get('passes') and mps['batched_seconds'] < cpu['batched_seconds'] else 'cpu'
    config = {'stage': 'revision_v3_exploratory', 'model': 'Qwen/Qwen3-Embedding-0.6B', 'revision': REVISION,
              'dtype': 'float32', 'device': device, 'batch_size': 4, 'max_padded_tokens': 4096,
              'threads': 2, 'interop_threads': 1, 'max_length': 8192, 'padding_side': 'left',
              'pooling': 'last_nonpadding_token', 'dimensions': 1024, 'normalize': True,
              'query_instruction': INSTRUCTION, 'document_instruction': None, 'attention': 'sdpa',
              'seed': SEED, 'deterministic_algorithms': True, 'use_cache': False,
              'input_sha256': sha_file(INPUT), 'source_sha256': sha_file(__file__),
              'scorer_sha256': sha_file(ROOT / 'src/evidence.py'), 'model_files': manifest,
              'dependencies': dependencies(), 'technical_plan_sha256': sha_file(OUT / 'technical_plan.md'),
              'technical_results_sha256': sha_file(OUT / 'technical_results.json'),
              'input_manifest_sha256': sha_file(OUT / 'input_manifest.json'),
              'ks': json.loads((ROOT / 'configs/main_v1.json').read_text())['ks']}
    freeze = {'utc': now(), 'config': config, 'cache_key': digest(config),
              'decision': 'Fastest passing technical backend, chosen before retrieval effectiveness',
              'effectiveness_computed': False, 'prior_two_hour_gate_removed_by_revision_instruction': True}
    write_json(OUT / 'runtime_freeze.json', freeze)
    (OUT / 'requirements.lock.txt').write_text('\n'.join(f'{k}=={v}' for k, v in sorted(config['dependencies'].items())) + '\n')
    print('Frozen', device, freeze['cache_key'], flush=True)


def read_freeze():
    freeze = json.loads((OUT / 'runtime_freeze.json').read_text())
    c = freeze['config']
    if c['source_sha256'] != sha_file(__file__) or c['input_sha256'] != sha_file(INPUT):
        raise ValueError('Frozen source/input mismatch')
    if c['scorer_sha256'] != sha_file(ROOT / 'src/evidence.py'):
        raise ValueError('Frozen scorer changed')
    if digest(c) != freeze['cache_key']:
        raise ValueError('Corrupt configuration key')
    return freeze


def cache_path(freeze):
    return OUT / 'cache' / freeze['cache_key']


def cached(path):
    if not path.exists():
        return False
    try:
        check_vectors(np.load(path, allow_pickle=False).reshape(1, -1), 1)
        return True
    except (OSError, ValueError):
        return False


def infer():
    torch = setup()
    freeze = read_freeze()
    c = freeze['config']
    if c['model_files'] != model_manifest() or c['dependencies'] != dependencies():
        raise ValueError('Frozen model/dependencies changed')
    texts, _ = collect_inputs(load_inputs())
    manifest = json.loads((OUT / 'input_manifest.json').read_text())
    lengths = manifest['lengths']
    cache = cache_path(freeze)
    cache.mkdir(parents=True, exist_ok=True)
    missing = [h for h in texts if not cached(cache / (h + '.npy'))]
    session = {'utc': now(), 'event': 'start', 'cache_key': freeze['cache_key'], 'already_cached': len(texts) - len(missing), 'missing': len(missing)}
    append(OUT / 'inference_sessions.jsonl', session)
    start = time.perf_counter()
    done = 0
    try:
        model, tok = instantiate(c['device'])
        for batch in batches(missing, lengths, c['batch_size'], c['max_padded_tokens']):
            arr = encode(model, tok, [texts[h] for h in batch], c['device'])
            for h, vec in zip(batch, arr):
                p = cache / (h + '.npy')
                tmp = p.with_suffix('.tmp')
                with tmp.open('wb') as f:
                    np.save(f, vec)
                tmp.replace(p)
            done += len(batch)
            if done % 200 < len(batch) or done == len(missing):
                status = {'utc': now(), 'event': 'progress', 'new_embeddings': done,
                          'completed': len(texts) - len(missing) + done, 'total': len(texts),
                          'elapsed_seconds': time.perf_counter() - start,
                          'peak_process_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
                if c['device'] == 'mps':
                    status['driver_mps_bytes'] = torch.mps.driver_allocated_memory()
                write_json(OUT / 'inference_status.json', status)
                print(json.dumps(status), flush=True)
    except Exception as exc:
        append(OUT / 'failures.jsonl', {'utc': now(), 'phase': 'inference', 'completed_new': done,
                                      'error': repr(exc), 'traceback': traceback.format_exc()})
        append(OUT / 'inference_sessions.jsonl', {'utc': now(), 'event': 'failed', 'new_embeddings': done, 'seconds': time.perf_counter() - start})
        raise
    finish = {'utc': now(), 'event': 'complete', 'new_embeddings': done, 'total': len(texts), 'seconds': time.perf_counter() - start}
    append(OUT / 'inference_sessions.jsonl', finish)
    fingerprints = {h: sha_file(cache / (h + '.npy')) for h in sorted(texts)}
    write_json(OUT / 'embedding_manifest.json', {'cache_key': freeze['cache_key'], 'files_sha256': fingerprints})
    write_json(OUT / 'inference_complete.json', {**finish, 'cache_key': freeze['cache_key'],
               'embedding_manifest_sha256': sha_file(OUT / 'embedding_manifest.json'), 'effectiveness_computed': False,
               'unique_truncated': manifest['truncated_unique_inputs'], 'max_model_tokens': manifest['max_model_tokens']})


def vector_map(freeze, texts):
    cache = cache_path(freeze)
    manifest = json.loads((OUT / 'embedding_manifest.json').read_text())
    if manifest['cache_key'] != freeze['cache_key'] or set(manifest['files_sha256']) != set(texts):
        raise ValueError('Incomplete/mismatched embedding manifest')
    vectors = {}
    for h in sorted(texts):
        path = cache / (h + '.npy')
        if sha_file(path) != manifest['files_sha256'][h]:
            raise ValueError('Cached vector content mismatch')
        vectors[h] = np.load(path, allow_pickle=False)
    check_vectors(np.stack(list(vectors.values())), len(vectors))
    return vectors


def score_all():
    from evidence import score, topology, completion_costs, digest as evidence_digest
    freeze = read_freeze()
    complete = json.loads((OUT / 'inference_complete.json').read_text())
    xs = load_inputs()
    texts, _ = collect_inputs(xs)
    if complete['total'] != len(texts):
        raise ValueError('Full inference is required before scoring')
    vectors = vector_map(freeze, texts)
    manifest = json.loads((OUT / 'input_manifest.json').read_text())
    lengths = manifest['lengths']
    rows, audits = [], []
    for x in xs:
        query = vectors[text_hash(query_text(x['query']))]
        doc = np.stack([vectors[text_hash(u)] for u in x['units']])
        scores = (doc @ query).astype(float).tolist()
        order = stable_order(scores)
        row = {'dataset': x['dataset'], 'split': x['split'], 'id': x['id'], 'cluster': x['cluster'], 'method': 'qwen3',
               'instance_hash': evidence_digest(x), 'config_hash': freeze['cache_key'], 'source_hash': freeze['config']['source_sha256'],
               'ranking': order, 'retrieval_scores': scores, 'gold': x['gold'], 'unit_count': len(x['units']),
               'metadata': x['metadata'], 'topology': topology(x['gold']),
               'costs': completion_costs(order, x['gold'], x['units']),
               'points': [{'k': k, 'retrieved_n': len(order[:k]), **score(order[:k], x['gold'])} for k in freeze['config']['ks']]}
        rows.append(row)
        unit_lengths = [lengths[text_hash(u)] for u in x['units']]
        audits.append({'dataset': x['dataset'], 'id': x['id'], 'query_tokens': lengths[text_hash(query_text(x['query']))],
                       'query_truncated': lengths[text_hash(query_text(x['query']))] > 8192,
                       'unit_model_tokens': unit_lengths, 'truncated_units': [i for i, n in enumerate(unit_lengths) if n > 8192],
                       'any_gold_truncated': any(unit_lengths[i] > 8192 for e in x['gold'] for i in e)})
    for name, values in [('rankings.jsonl', rows), ('truncation.jsonl', audits)]:
        path = OUT / name
        data = ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True) + '\n' for r in values)
        if path.exists() and path.read_text() != data:
            raise ValueError('Scoring replay mismatch; old output retained')
        path.write_text(data)
    write_json(OUT / 'scoring_complete.json', {'utc': now(), 'stage': 'revision_v3_exploratory', 'rankings': len(rows),
               'points': sum(len(r['points']) for r in rows), 'counts': dict(collections.Counter(x['dataset'] for x in xs)),
               'rankings_sha256': sha_file(OUT / 'rankings.jsonl'), 'truncation_sha256': sha_file(OUT / 'truncation.jsonl')})
    print('Scored all', len(rows), 'items; rankings:', OUT / 'rankings.jsonl', flush=True)


def validate():
    from evidence import score, completion_costs, digest as evidence_digest
    freeze = read_freeze()
    xs = {(x['dataset'], x['id']): x for x in load_inputs()}
    rows = [json.loads(s) for s in (OUT / 'rankings.jsonl').read_text().splitlines()]
    keys = [(r['dataset'], r['id']) for r in rows]
    assert len(keys) == len(set(keys)) == len(xs) and set(keys) == set(xs)
    counts = collections.Counter()
    for r in rows:
        x = xs[(r['dataset'], r['id'])]
        assert r['instance_hash'] == evidence_digest(x)
        assert r['cluster'] == x['cluster'] and r['gold'] == x['gold']
        n = len(x['units'])
        assert sorted(r['ranking']) == list(range(n)) and len(r['retrieval_scores']) == n
        assert r['ranking'] == stable_order(r['retrieval_scores'])
        assert x['gold'] and all(e and set(e) <= set(range(n)) for e in x['gold'])
        assert r['costs'] == completion_costs(r['ranking'], x['gold'], x['units'])
        for p in r['points']:
            assert {k: v for k, v in p.items() if k not in {'k', 'retrieved_n'}} == score(r['ranking'][:p['k']], x['gold'])
        for k in range(n + 1):
            p = score(r['ranking'][:k], x['gold'])
            assert p['union_complete'] <= p['complete'] <= p['hit']
            if len({frozenset(e) for e in x['gold']}) == 1:
                assert p['complete'] == p['union_complete']
            counts['integer_prefix_checks'] += 1
    report = {'utc': now(), 'passed': True, 'rankings': len(rows), 'scoring_points': sum(len(r['points']) for r in rows),
              **dict(counts), 'rankings_sha256': sha_file(OUT / 'rankings.jsonl'),
              'checks': ['original item IDs and annotation hashes', 'source-index tie breaking', 'full candidate permutations',
                         'nonempty valid evidence families', 'all-prefix A<=C<=H', 'single-distinct-set C=A',
                         'cost replay', 'all six original unit budgets'], 'cache_key': freeze['cache_key']}
    write_json(OUT / 'validation.json', report)
    print(json.dumps(report), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('command', choices=['technical', 'infer', 'score', 'validate'])
    args = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    {'technical': technical, 'infer': infer, 'score': score_all, 'validate': validate}[args.command]()


if __name__ == '__main__':
    main()

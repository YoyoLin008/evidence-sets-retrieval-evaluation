"""Acquire only pinned Qwen files, without depending on the v2 ecosystem audit.

Run with --verify-only to hash-check the existing local model without networking.
No weights are redistributed by this repository. Original files with unexpected
hashes are never overwritten. Uses the original model manifest and revision.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'revisions/v2/compute'
OUT = ROOT / 'revisions/v3/encoder'


def sha_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def get_checked(url, path, expected, verify_only=False):
    if path.exists():
        if sha_file(path) != expected:
            raise ValueError(f'Existing model file has an unexpected hash: {path.name}; retained unchanged')
        return 'verified-existing'
    if verify_only:
        raise FileNotFoundError(f'Missing pinned model file: {path.name}')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.download-part')
    request = urllib.request.Request(url, headers={'User-Agent': 'EvidenceMeasurementResearch/3.0'})
    h = hashlib.sha256()
    try:
        with urllib.request.urlopen(request, timeout=180) as response, temporary.open('wb') as f:
            for block in iter(lambda: response.read(1024 * 1024), b''):
                h.update(block)
                f.write(block)
        if h.hexdigest() != expected:
            raise ValueError(f'Download checksum mismatch for {path.name}; no destination file written')
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return 'downloaded-and-verified'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    manifest_path = BASE / 'model_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    revision = json.loads((BASE / 'runtime_freeze.json').read_text())['config']['revision']
    v3freeze = OUT / 'runtime_freeze.json'
    if v3freeze.exists() and json.loads(v3freeze.read_text())['config']['revision'] != revision:
        raise ValueError('Revision mismatch between original acquisition and v3 encoder freeze')
    rows = []
    for name, expected in sorted(manifest.items()):
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid relative model-manifest path')
        url = f'https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/resolve/{revision}/{name}'
        path = BASE / 'model' / relative
        status = get_checked(url, path, expected, args.verify_only)
        rows.append({'file': name, 'url': url, 'sha256': expected, 'size_bytes': path.stat().st_size, 'status': status})
        print(f'{name}: {status}', flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'revision': revision,
              'original_manifest_sha256': sha_file(manifest_path), 'verify_only': args.verify_only,
              'files': rows, 'scope': 'Pinned local model and tokenizer files; no inference or effectiveness.'}
    (OUT / 'acquisition_verification.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')


if __name__ == '__main__':
    main()

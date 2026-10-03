"""Meaningful cache/input/pooling/order checks independent of effectiveness."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('revision_v3_encoder', Path(__file__).resolve().parents[1] / 'src/revision_v3_encoder.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


def test_roles_dedup_and_instruction():
    xs = [{'query': 'same', 'units': ['same', 'same', 'other']}]
    texts, roles = e.collect_inputs(xs)
    assert len(texts) == 3
    assert roles[e.text_hash('same')] == {'document': 2}
    assert roles[e.text_hash(e.query_text('same'))] == {'query': 1}
    assert e.query_text('same') == 'Instruct: ' + e.INSTRUCTION + '\nQuery:same'


def test_bounded_batches_preserve_every_input_and_order():
    lengths = {'a': 8000, 'b': 2200, 'c': 2000, 'd': 20, 'e': 20, 'f': 30}
    batches = list(e.batches(list(lengths), lengths, 4, 4096))
    flat = [h for b in batches for h in b]
    assert flat == sorted(lengths, key=lambda h: (lengths[h], h))
    assert len(flat) == len(set(flat))
    for b in batches:
        assert len(b) <= 4
        assert len(b) == 1 or len(b) * max(lengths[h] for h in b) <= 4096


def test_ties_and_nonfinite_rejected():
    assert e.stable_order([.2, .7, .7, -.1]) == [1, 2, 0, 3]
    with pytest.raises(ValueError):
        e.stable_order([float('nan')])


def test_cache_fingerprint_changes_with_inputs_or_settings():
    config = {'source_sha256': 'a', 'revision': 'r', 'device': 'cpu', 'instruction': 'q'}
    for key in config:
        assert e.digest(config) != e.digest({**config, key: 'different'})
    assert e.digest(config) == e.digest(dict(reversed(list(config.items()))))


def test_cache_rejects_incomplete_invalid_or_unnormalized(tmp_path):
    p = tmp_path / 'x.npy'
    assert not e.cached(p)
    p.write_bytes(b'partial')
    assert not e.cached(p)
    np.save(p, np.zeros(1024, dtype=np.float32))
    assert not e.cached(p)
    vec = np.zeros(1024, dtype=np.float32)
    vec[0] = 1
    np.save(p, vec)
    assert e.cached(p)


def test_last_token_mask_left_right_mixed_and_empty():
    torch = pytest.importorskip('torch')
    hidden = torch.arange(24, dtype=torch.float32).reshape(2, 4, 3)
    for mask, expected in [([[0,0,1,1],[0,1,1,1]], hidden[:, -1]),
                           ([[1,1,0,0],[1,1,1,0]], torch.stack([hidden[0,1], hidden[1,2]])),
                           ([[0,0,1,1],[1,1,0,0]], torch.stack([hidden[0,3], hidden[1,1]]))]:
        assert torch.equal(e.last_token_pool(hidden, torch.tensor(mask)), expected)
    with pytest.raises(ValueError):
        e.last_token_pool(hidden, torch.zeros((2,4), dtype=torch.long))


def acquire_helper():
    spec = importlib.util.spec_from_file_location('revision_v3_encoder_acquire', Path(__file__).resolve().parents[1] / 'src/revision_v3_encoder_acquire.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_acquisition_preserves_existing_mismatch_and_verify_only(tmp_path):
    a = acquire_helper()
    path = tmp_path / 'model'
    path.write_bytes(b'existing')
    with pytest.raises(ValueError, match='retained unchanged'):
        a.get_checked('https://example.invalid/not-requested', path, '0' * 64, True)
    assert path.read_bytes() == b'existing'
    with pytest.raises(FileNotFoundError):
        a.get_checked('https://example.invalid/not-requested', tmp_path / 'missing', '0' * 64, True)
    assert a.get_checked('https://example.invalid/not-requested', path, a.sha_file(path), True) == 'verified-existing'


def test_acquisition_stream_hash_before_promoting(tmp_path):
    a = acquire_helper()
    source = tmp_path / 'source'
    source.write_bytes(b'fixture payload')
    destination = tmp_path / 'new' / 'weights'
    with pytest.raises(ValueError, match='checksum mismatch'):
        a.get_checked(source.as_uri(), destination, '0' * 64)
    assert not destination.exists()
    assert not destination.with_name('weights.download-part').exists()
    assert a.get_checked(source.as_uri(), destination, a.sha_file(source)) == 'downloaded-and-verified'
    assert destination.read_bytes() == source.read_bytes()

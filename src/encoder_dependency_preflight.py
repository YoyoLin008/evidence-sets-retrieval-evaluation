"""Read-only exact dependency preflight for the unchanged frozen Qwen encoder.

Run with the intended encoder environment. Does not acquire or load model
weights, run inference, create a freeze, or write result/cache files.
"""
from pathlib import Path
import hashlib
import json
import platform
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def main():
    freeze = json.loads((ROOT / 'revisions/v3/encoder/runtime_freeze.json').read_text())
    expected = freeze['config']['dependencies']
    try:
        # Call the published function unchanged; importing it does not run main.
        from revision_v3_encoder import dependencies
        observed = dependencies()
    except ImportError as error:
        print(json.dumps({'passed': False, 'error': str(error),
                          'scope': 'dependency preflight; no inference'}, indent=2))
        return 1
    missing = {k: v for k, v in expected.items() if k not in observed}
    unexpected = {k: v for k, v in observed.items() if k not in expected}
    mismatched = {k: {'expected': v, 'observed': observed[k]}
                  for k, v in expected.items() if k in observed and observed[k] != v}
    source_checks = {
        filename: hashlib.sha256((ROOT / 'src' / filename).read_bytes()).hexdigest() == freeze['config'][key]
        for filename, key in [('revision_v3_encoder.py', 'source_sha256'), ('evidence.py', 'scorer_sha256')]
    }
    config_file = Path(sys.prefix) / 'pyvenv.cfg'
    isolated = (sys.prefix != sys.base_prefix and config_file.is_file()
                and 'include-system-site-packages = false' in config_file.read_text().lower())
    exact_match = observed == expected
    report = {'scope': 'fresh-environment installation and dependency-preflight validation; not full inference replication',
              'passed': exact_match and all(source_checks.values()) and isolated,
              'python': sys.version, 'implementation': platform.python_implementation(),
              'platform': platform.platform(), 'machine': platform.machine(),
              'environment_name': Path(sys.prefix).name,
              'isolated_virtual_environment': isolated,
              'expected_distribution_count': len(expected), 'observed_distribution_count': len(observed),
              'exact_dictionary_match': exact_match, 'missing': missing, 'unexpected': unexpected,
              'version_mismatches': mismatched, 'frozen_sources_match': source_checks,
              'observed_dependencies': observed, 'inference_started': False}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

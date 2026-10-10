#!/usr/bin/env python3
"""Pack or restore text-only research evidence without data, weights or photos."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'artifacts/evidence/execution_evidence_20261010.zip'
MANIFEST = ARCHIVE.with_suffix('.manifest.json')
RUNS = (
    'p0_20261010_111919', 'p0_recheck_20261010_113854_OTajtv',
    'p1_20261010_132030', 'p1_recheck_20261010_133612_JLRNvs',
    'p2_20261010_134300', 'p2_recheck_20261010_135136_H3hH4C',
    'p3_dinov2_20261010_140000', 'p3_dinov2_stable_20261010_141000',
    'p3_eigenplaces_20261010_141736_ayAvV5', 'p3_eigenplaces_20261010_141715_Y5tpTg',
    'freeze_review_20261010_143800', 'p4_frozen_20261010_152754_Z1p6iu',
    'p5_pdf_acceptance_20261010_193746',
)
SUFFIXES = {'.json', '.jsonl', '.csv', '.log', '.md', '.txt', '.yaml', '.py', '.sh', '.tex', '.xml'}
SKIP_PARTS = {'figures', 'figures_readable_v2', 'synthetic_cache_corruption_probes'}
PATTERNS = {
    'private_key': r'-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----',
    'github_token': r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
    'openai_token': r'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{25,}\b',
    'aws_access_key': r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'url_credentials': r'https?://[^\s/@:]+:[^\s/@]+@',
    'credential_query': r'[?&](?:token|secret|password|auth)=[A-Za-z0-9_%-]{12,}',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pack():
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    assert not ARCHIVE.exists() and not MANIFEST.exists(), 'Immutable snapshot already exists.'
    files = []
    for name in RUNS:
        directory = ROOT / 'outputs' / name
        assert directory.is_dir(), name
        files.extend(p for p in directory.rglob('*') if p.is_file() and not p.is_symlink()
                     and p.suffix in SUFFIXES and not SKIP_PARTS.intersection(p.parts))
    hashes = {}
    for path in sorted(files):
        content = path.read_bytes()
        text = content.decode('utf-8')
        for kind, pattern in PATTERNS.items():
            assert not re.search(pattern, text), f'Possible credential ({kind}) in {path.name}; value not printed.'
        assert len(content) < 100 * 1024 ** 2
        hashes[str(path.relative_to(ROOT))] = digest(content)
    with zipfile.ZipFile(ARCHIVE, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(files):
            bundle.write(path, str(path.relative_to(ROOT)))
    assert ARCHIVE.stat().st_size < 50 * 1024 ** 2, 'Keep this archive below 50 MiB.'
    manifest = {
        'scope': 'Original text-only P0-P5 research outputs, including nonzero attempts; no reruns.',
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'archive': str(ARCHIVE.relative_to(ROOT)), 'archive_sha256': digest(ARCHIVE.read_bytes()),
        'archive_bytes': ARCHIVE.stat().st_size, 'file_count': len(files),
        'excluded': ['Raw datasets', 'Model weights', 'Descriptor arrays', 'Virtual environments',
                     'Dataset photos and matching photo strips', 'Original website frontend copies',
                     'Third-party source trees', 'Duplicate plot layouts', 'Prior full handoff ZIPs'],
        'sensitive_pattern_scan': 'No findings in all selected UTF-8 evidence files; not a guarantee beyond listed patterns.',
        'file_sha256': hashes,
    }
    with MANIFEST.open('x') as stream:
        json.dump(manifest, stream, indent=2)
    verify(manifest)
    print(json.dumps({k: manifest[k] for k in ('archive', 'archive_bytes', 'archive_sha256', 'file_count')}))


def verify(manifest):
    assert digest(ARCHIVE.read_bytes()) == manifest['archive_sha256']
    with zipfile.ZipFile(ARCHIVE) as bundle:
        assert bundle.testzip() is None
        assert set(bundle.namelist()) == set(manifest['file_sha256'])
        for name, expected in manifest['file_sha256'].items():
            relative = Path(name)
            assert not relative.is_absolute() and '..' not in relative.parts
            assert relative.parts[0] == 'outputs'
            assert digest(bundle.read(name)) == expected, name


def restore(destination):
    manifest = json.loads(MANIFEST.read_text())
    verify(manifest)
    destination = destination.resolve()
    with zipfile.ZipFile(ARCHIVE) as bundle:
        # Preflight every existing file before writing any new evidence.
        for name, expected in manifest['file_sha256'].items():
            path = destination / name
            assert path.resolve().is_relative_to(destination), name
            assert not path.is_symlink(), name
            if path.exists():
                assert path.is_file() and digest(path.read_bytes()) == expected, f'Existing evidence differs: {name}'
        written = 0
        for name in manifest['file_sha256']:
            path = destination / name
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(bundle.read(name))
                written += 1
    print(json.dumps({'verified_files': manifest['file_count'], 'newly_restored_files': written,
                      'destination': str(destination), 'models_or_datasets_restored': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('pack', 'verify', 'restore'))
    parser.add_argument('--destination', type=Path, default=ROOT)
    args = parser.parse_args()
    if args.action == 'pack':
        pack()
    elif args.action == 'restore':
        restore(args.destination)
    else:
        manifest = json.loads(MANIFEST.read_text())
        verify(manifest)
        print(json.dumps({'passed': True, 'verified_files': manifest['file_count']}))


if __name__ == '__main__':
    main()

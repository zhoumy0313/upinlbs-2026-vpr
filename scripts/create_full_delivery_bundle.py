#!/usr/bin/env python3
"""Snapshot existing public research evidence; no experiments or model fitting."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

from frozen_package import validate_package

ROOT = Path(__file__).resolve().parents[1]
HISTORY = (
    'p0_20261010_111919', 'p0_recheck_20261010_113854_OTajtv',
    'p1_20261010_132030', 'p1_recheck_20261010_133612_JLRNvs',
    'p2_20261010_134300', 'p2_recheck_20261010_135136_H3hH4C',
    'p3_dinov2_20261010_140000', 'p3_dinov2_stable_20261010_141000',
    'p3_eigenplaces_20261010_141736_ayAvV5',
    'p3_eigenplaces_20261010_141715_Y5tpTg',
)
P4 = ROOT / 'outputs/p4_frozen_20261010_152754_Z1p6iu'
PACKAGE = ROOT / 'outputs/freeze_review_20261010_143800/selection.json'
SUFFIXES = {'.json', '.jsonl', '.csv', '.log', '.md', '.txt', '.py', '.yaml', '.tex',
            '.sh', '.js', '.html'}
FORBIDDEN = {'weights', 'third_party', 'raw', 'downloads', '.git', '__pycache__'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, obj):
    with path.open('x') as stream:
        json.dump(obj, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def select(directory):
    return {p for p in directory.rglob('*') if p.is_file() and p.suffix in SUFFIXES}


def coverage(directory, files):
    command_files = sorted(directory.rglob('commands.jsonl'))
    events = [json.loads(line) for p in command_files
              for line in p.read_text().splitlines() if line.strip()]
    for event in events:
        assert isinstance(event['exit_status'], int)
        assert event.get('argv') and event.get('started_at') and event.get('ended_at')
        log = directory / event['log']
        assert log in files, f'Missing recorded command log: {log}'
    tests = {}
    for log in sorted(directory.rglob('*tests*.log')):
        counts = re.findall(r'(\d+) passed(?:,| in)', log.read_text())
        if counts:
            tests[str(log.relative_to(ROOT))] = int(counts[-1])
    return {
        'selected_files': sum(directory in p.parents for p in files),
        'recorded_commands': len(events),
        'nonzero_commands': [{'name': e['name'], 'exit_status': e['exit_status']}
                             for e in events if e['exit_status'] != 0],
        'historical_pytest_pass_counts': tests,
        'note': 'Original results, not new executions; retained nonzero attempts are included.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--paper-acceptance', type=Path,
                        help='Include a separately inspected user-exported paper PDF and its audit.')
    args = parser.parse_args()
    if args.paper_acceptance:
        args.paper_acceptance = args.paper_acceptance.resolve()
    out = args.output_dir.resolve()
    assert out.parent == ROOT / 'outputs', 'Use a fresh directory under project outputs.'
    out.mkdir(exist_ok=True)
    archive = out / 'UPINLBS_full_evidence_working_draft.zip'
    assert not archive.exists()
    validate_package(PACKAGE)
    acceptance = json.loads((P4 / 'phase_acceptance.json').read_text())
    replay = json.loads((P4 / 'phase_acceptance_replay_v2.json').read_text())
    for key in ('passed', 'offline_rows', 'online_rows', 'policy_radius_evaluations',
                'outcomes', 'source_sha256', 'package_sha256'):
        assert acceptance[key] == replay[key]
    assert acceptance['passed']
    rendering = json.loads((P4 / 'rendering_acceptance.json').read_text())
    assert rendering['passed'] and rendering['paper_source_sha256'] == sha(ROOT / 'paper/main.tex')
    paper_acceptance = None
    if args.paper_acceptance:
        paper_acceptance = json.loads(args.paper_acceptance.read_text())
        assert paper_acceptance['passed'] and 1 <= paper_acceptance['pages'] <= 6
        assert paper_acceptance['pdf_sha256'] == sha(ROOT / 'paper/main.pdf')
        assert paper_acceptance['source_sha256'] == sha(ROOT / 'paper/main.tex')
        assert paper_acceptance['all_pages_rendered_and_visually_reviewed']
    else:
        assert not (ROOT / 'paper/main.pdf').exists(), 'PDF arrived: provide its validated acceptance.'
    tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
    files = {ROOT / p for p in tracked
             if Path(p).parts[0] in {'src', 'scripts', 'tests', 'configs', 'docs', 'paper', 'data'}
             or p in {'PLAN.md', 'AGENTS.md', 'README.md', 'pyproject.toml', '.gitignore'}}
    for name in HISTORY:
        directory = ROOT / 'outputs' / name
        assert directory.is_dir(), directory
        files.update(select(directory))
    toy_figures = ROOT / 'outputs/p0_recheck_20261010_113854_OTajtv/official_toy/2026-10-10_11-39-02/preds'
    toy_examples = list(toy_figures.glob('*.jpg'))
    assert len(toy_examples) == 5
    files.update(toy_examples)
    files.update(select(PACKAGE.parent))
    files.update(p for p in select(P4)
                 if not {'figures', 'figures_readable_v2'} & set(p.parts)
                 and p.name not in {'delivery_manifest.json', 'bundle_identity.json', 'bundle_acceptance.json'})
    files.update(p for p in (P4 / 'figures_readable_v3').iterdir() if p.is_file())
    if paper_acceptance:
        files.add(ROOT / 'paper/main.pdf')
        files.update(select(args.paper_acceptance.parent))
        files.update(args.paper_acceptance.parent.glob('page-*.png'))
        files.add(args.paper_acceptance.parent / 'uploaded_document.pdf')
    for p in files:
        parts = p.relative_to(ROOT).parts
        assert not FORBIDDEN & set(parts) and not any(c.startswith('.venv') for c in parts)
        assert p.suffix not in {'.npy', '.pt', '.pth', '.zip'}
        assert p.is_file() and not p.is_symlink()
    stages = {name: coverage(ROOT / 'outputs' / name, files) for name in HISTORY}
    stages[P4.name] = coverage(P4, files)
    if paper_acceptance:
        stages[args.paper_acceptance.parent.name] = coverage(args.paper_acceptance.parent, files)
    assert all(stages[n]['recorded_commands'] for n in HISTORY[:-1])
    assert (ROOT / 'outputs' / HISTORY[-1] / 'bootstrap_failure.json') in files
    stage_path = out / 'stage_coverage.json'
    write_new(stage_path, stages)
    files.add(stage_path)
    inventory = {
        'scope': 'Full local source and P0-P4 evidence snapshot, including failed attempts.',
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'freeze_package_sha256': sha(PACKAGE), 'paper_source_sha256': sha(ROOT / 'paper/main.tex'),
        'final_experiments_verified': True, 'paper_pdf_included': bool(paper_acceptance),
        'local_working_draft_complete': bool(paper_acceptance), 'submission_ready': False,
        'excluded': ['Bulk datasets', 'Model checkpoints', 'Virtual environments', 'Descriptor arrays',
                     'Authentication files', 'Active bundle-generation log'],
        'missing_local_working_draft_artifacts': [] if paper_acceptance else
                    ['Exported paper PDF with verified <=6 total pages, fonts and layout'],
        'remaining_author_review': ['Authorship/correspondence, contribution, interpretation and submission details'],
        'paper_pdf_acceptance': paper_acceptance,
        'experiment_rows': {k: acceptance[k] for k in
                            ('offline_rows', 'online_rows', 'policy_radius_evaluations')},
        'source_and_artifact_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sorted(files)},
    }
    manifest = out / 'delivery_manifest.json'
    write_new(manifest, inventory)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in sorted(files):
            bundle.write(path, str(path.relative_to(ROOT)))
        bundle.write(manifest, str(manifest.relative_to(ROOT)))
    # Read back compressed bytes rather than accepting the writer's in-memory inventory.
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        expected = inventory['source_and_artifact_sha256']
        assert set(bundle.namelist()) == set(expected) | {str(manifest.relative_to(ROOT))}
        for name, expected_sha in expected.items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == expected_sha, name
        assert bundle.read('paper/main.tex') == (ROOT / 'paper/main.tex').read_bytes()
    summary = {
        'passed': True, 'archive': str(archive), 'bytes': archive.stat().st_size,
        'sha256': sha(archive), 'file_count': len(files) + 1,
        'stage_roots': len(stages), 'recorded_commands': sum(s['recorded_commands'] for s in stages.values()),
        'retained_nonzero_commands': sum(len(s['nonzero_commands']) for s in stages.values()),
        'crc_and_every_file_sha256_verified': True, 'paper_pdf_included': bool(paper_acceptance),
        'local_working_draft_complete': bool(paper_acceptance), 'submission_ready': False,
    }
    write_new(out / 'bundle_acceptance.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

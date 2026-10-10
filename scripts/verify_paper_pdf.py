#!/usr/bin/env python3
"""Check the user-exported working-draft PDF against logged experiment tables."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numbers(line):
    return re.findall(r'\d+\.\d{2}', line)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf-run', type=Path, required=True)
    parser.add_argument('--experiment-run', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--acceptance-output', default='pdf_acceptance.json')
    args = parser.parse_args()
    out, final = args.pdf_run, args.experiment_run
    receipt = read(out / 'receipt.json')
    pdf = out / 'uploaded_document.pdf'
    assert sha(pdf) == receipt['pdf_sha256']
    assert sha(args.source) == receipt['paper_source_sha256']
    assert sha(args.source) == read(final / 'paper_draft_provenance.json')['source_sha256']
    assert read(final / 'phase_acceptance.json')['passed']
    assert read(final / 'phase_acceptance_replay_v2.json')['passed']
    info = (out / 'pdf_information.log').read_text()
    pages = int(re.search(r'^Pages:\s+(\d+)', info, re.M)[1])
    assert 1 <= pages <= 6
    assert re.search(r'^Encrypted:\s+no$', info, re.M)
    font_lines = (out / 'pdf_fonts.log').read_text().splitlines()
    fonts = []
    for line in font_lines:
        fields = line.split()
        if len(fields) >= 8 and fields[-2:].count('0') == 1 and fields[-2].isdigit():
            assert fields[-5] == 'yes', line
            assert 'Type 3' not in line, line
            fonts.append({'name': fields[0], 'embedded': True, 'raw': line})
    assert fonts, 'No embedded-font inventory parsed.'
    text = unicodedata.normalize('NFKC', (out / 'paper_text.txt').read_text())
    assert len([p for p in text.split('\f') if p.strip()]) == pages
    for marker in ('When Is a Second Visual Encoder Worth Calling?', 'Mingyang Zhou',
                   'University of Chinese Academy of Sciences', 'ACKNOWLEDGMENT',
                   '107100', '85000', '78.92%', '15.50%', '10.31%',
                   'OpenAI Codex', 'human author review'):
        assert marker in text, marker
    assert re.search(r'^\s*R\s*EFERENCES\s*$', text, re.M)
    assert not re.search(r'\[\?\??\]|\bTODO\b|\bTBD\b', text)
    assert len(re.findall(r'^\[\d+\]', text, re.M)) == 8
    for name in ('baseline_table.tex', 'final_table.tex', 'cost_figure.tex'):
        fragment = (final / 'paper_elements' / name).read_text()
        assert fragment in args.source.read_text(), name
    assert len(list(out.glob('page-*.png'))) == pages
    visual = read(out / 'visual_review.json')
    assert [p['page'] for p in visual['pages']] == list(range(1, pages + 1))
    assert not visual['obvious_clipping_or_overlap_observed']
    table2 = text.split('TABLE II\n', 1)[1].split('TABLE III\n', 1)[0]
    table3 = text.split('TABLE III\n', 1)[1].split('mean-latency saving.', 1)[0]
    tables = []

    def verify_row(table, label, expected):
        rows = [line.strip() for line in table.splitlines() if line.strip().startswith(label)]
        assert len(rows) == 1, (label, rows)
        actual = numbers(rows[0])
        wanted = [f'{n:.2f}' for n in expected]
        assert actual == wanted, (label, actual, wanted)
        tables.append({'label': label, 'pdf_values': actual, 'matched_experiment_values': True})

    datasets = ('nordland', 'gardens')
    data = {}
    for dataset in datasets:
        p = final / 'results' / dataset / 'pair_eigenplaces'
        acc = read(p / 'accuracy.json')
        data[dataset] = (acc['by_radius'][str(acc['primary_radius'])],
                         acc['random_all_seeds'], read(p / 'latency.json')['policies'])
    for label, pair, policy in (('CosPlace R18', 'eigenplaces', 'A_only'),
                               ('EigenPlaces R50', 'eigenplaces', 'B_only'),
                               ('DINOv2 ViT-S/14 CLS', 'dinov2', 'B_only')):
        values = []
        for dataset in datasets:
            a = read(final / 'results' / dataset / ('pair_' + pair) / 'accuracy.json')
            v = a['by_radius'][str(a['primary_radius'])][policy]
            values.extend(100 * v[f'R@{k}'] for k in (1, 5, 10))
        verify_row(table2, label, values)
    policies = [('A-only', 'A_only'), ('EigenPlaces-only', 'B_only')]
    policies += [(f'Benefit ({b}%)', f'net_benefit_budget{b:02d}') for b in (10, 25, 50)]
    policies += [(f'A-error ({b}%)', f'trained_A_error_budget{b:02d}') for b in (10, 25, 50)]
    policies += [('Gap (25%)', 'gap_budget25'), ('Rescue only (25%)', 'rescue_only_budget25'),
                 ('Benefit, no std (25%)', 'net_benefit_no_std_budget25')]
    for label, policy in policies:
        values = []
        for dataset in datasets:
            accuracy, _, latency = data[dataset]
            v = accuracy[policy]
            values.extend((100 * v['R@1'], 100 * v['invocation_fraction'], latency[policy]['mean_ms']))
        verify_row(table3, label, values)
    for label, family in (('Random, nominal 25%', 'random_budget'),
                          ('Random, validation-matched', 'random_matched_net')):
        values = []
        for dataset in datasets:
            _, random, latency = data[dataset]
            prefix = family + '_budget25'
            v = random[prefix]
            values.extend((100 * v['R@1']['mean'], 100 * v['R@1']['std_population'],
                           100 * v['invocation_fraction']['mean'],
                           sum(latency[prefix + f'_seed{s}']['mean_ms'] for s in range(5)) / 5))
        verify_row(table3, label, values)
    result = {
        'passed': True, 'scope': 'Five-page English experimental working draft; not submission or human-author approval.',
        'pdf_sha256': sha(pdf), 'source_sha256': sha(args.source), 'pages': pages,
        'references_included_in_page_count': True, 'paper_size': 'US Letter, 612 x 792 pt',
        'embedded_fonts': fonts, 'type3_fonts_present': False,
        'all_pages_rendered_and_visually_reviewed': True,
        'final_table_rows_verified': tables, 'final_numeric_cells_verified': sum(len(t['pdf_values']) for t in tables),
        'figure_source_point_count': sum(len(p) for p in read(final / 'paper_elements/provenance.json')['point_sources'].values()),
        'source_fragments_match_logged_provenance': True,
        'author_submission_review_complete': False,
        'remaining_author_review': ['Other authors and correspondence', 'Contribution and interpretation',
                                    'Official anonymity, paper-size and exact deadline details'],
        'commands_checked': {e['name']: e['exit_status'] for e in
                             map(json.loads, (out / 'commands.jsonl').read_text().splitlines())},
    }
    for name in ('pdf_information', 'pdf_fonts', 'pdf_text', 'render_all_pages'):
        assert result['commands_checked'][name] == 0
    result['retained_nonzero_attempts'] = {k: v for k, v in result['commands_checked'].items() if v != 0}
    assert result['retained_nonzero_attempts'] in ({}, {'verify_exported_paper': 1})
    assert Path(args.acceptance_output).name == args.acceptance_output
    with (out / args.acceptance_output).open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({k: result[k] for k in ('passed', 'pages', 'final_numeric_cells_verified', 'figure_source_point_count')}))


if __name__ == '__main__':
    main()

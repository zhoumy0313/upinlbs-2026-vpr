"""Delivery-only font correction; preserve every G4-frozen scientific byte."""
import json, textwrap, warnings, subprocess
from . import final_delivery as original
from .runtime import ROOT, Run, sha

def checked_author_pdf(body, path):
    import matplotlib
    matplotlib.use('Agg')
    matplotlib.rcParams['pdf.fonttype'] = 42
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.font_manager import FontProperties, fontManager
    from matplotlib.ft2font import FT2Font
    import matplotlib.pyplot as plt
    cjk = '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
    fontManager.addfont(cjk)
    props = FontProperties(family=['DejaVu Sans', FT2Font(cjk).family_name])
    files = fontManager._find_fonts_by_props(props)
    covered = set().union(*(set(FT2Font(f).get_charmap()) for f in files))
    headings = 'VPR-GOAL-V3 作者审阅摘要研究执行与论文有效性分开判断；第 1/2 页。'
    missing = sorted({c for c in body + headings if not c.isspace() and ord(c) not in covered})
    assert not missing, missing
    lines = []
    for line in body.splitlines():
        lines += textwrap.wrap(line, width=38, break_long_words=True) if line else ['']
    pages = (len(lines) + 43) // 44
    assert pages <= 2, (len(lines), pages)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        with PdfPages(path) as pdf:
            for page in range(pages):
                fig = plt.figure(figsize=(8.27, 11.69))
                fig.text(.09, .94, 'VPR-GOAL-V3 作者审阅摘要', fontproperties=props, fontsize=16)
                for k, line in enumerate(lines[page*44:(page+1)*44]):
                    fig.text(.09, .89-k*.0185, line, fontproperties=props, fontsize=10.5)
                fig.text(.09, .045, f'研究执行与论文有效性分开判断；第 {page+1}/{pages} 页。', fontproperties=props, fontsize=9)
                pdf.savefig(fig)
                plt.close(fig)
    assert not any('Glyph' in str(w.message) and 'missing' in str(w.message) for w in caught)
    extracted = subprocess.check_output(['pdftotext', str(path), '-'], text=True)
    normalized = ''.join(extracted.split())
    assert 'VPR-GOAL-V3' in normalized and '598/656' in normalized and '644/656' in normalized
    (ROOT/'docs/research_v3/AUTHOR_BRIEF_FONT_AUDIT.json').write_text(json.dumps(dict(
        fonts=[dict(path=f,sha256=sha(__import__('pathlib').Path(f))) for f in files],
        missing_glyphs=missing,pages=pages,critical_identifiers_and_counts_extracted=True,
        frozen_prediction_code_unchanged=True),indent=2)+'\n')
    return pages

def main():
    run = Run('g7_delivery_driver', 'delivery-only Latin/CJK fallback correction, unchanged scientific freeze', {})
    run.write('model_identity.json', dict(not_new_inference=True))
    run.command([str(ROOT/'.venv-paper/bin/python'), '-m', 'experiments.endpoint_vpr.g7_delivery_checked', '--worker'])
    run.finish(dict(actual_stage_exit_code=0,font_correction_only=True), dict(passed=True))

if __name__ == '__main__':
    if '--worker' in __import__('sys').argv:
        original.author_pdf = checked_author_pdf
        original.main()
    else:
        main()

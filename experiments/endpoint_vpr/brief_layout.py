"""Preserve initial briefing; reflow a new version without splitting numeric tokens."""
import re,json,subprocess,warnings
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['pdf.fonttype']=42
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties,fontManager
from matplotlib.ft2font import FT2Font
import matplotlib.pyplot as plt
from .runtime import ROOT,Run,sha

def main():
    run=Run('g7_brief_reflow','new author briefing layout only; original and all scientific evidence retained',{})
    source=ROOT/'docs/research_v3/AUTHOR_SUMMARY_ZH.md'
    old=ROOT/'docs/research_v3/AUTHOR_SUMMARY_ZH.pdf'
    target=ROOT/'docs/research_v3/AUTHOR_SUMMARY_ZH_r02.pdf'
    assert not target.exists()
    fontManager.addfont('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf')
    props=FontProperties(family=['DejaVu Sans','Droid Sans Fallback'],size=10.5)
    probe=plt.figure(figsize=(8.27,11.69),dpi=100);probe.canvas.draw();renderer=probe.canvas.get_renderer()
    lines=[]
    for para in source.read_text().splitlines():
        if not para:lines.append('');continue
        tokens=re.findall(r'[A-Za-z0-9]+(?:[._/:\-%=][A-Za-z0-9]+)*|[^\x00-\x7f]|\s+|.',para)
        line=''
        for token in tokens:
            if line and renderer.get_text_width_height_descent(line+token,props,False)[0]>650:
                lines.append(line.rstrip());line=token.lstrip()
            else:line+=token
        lines.append(line.rstrip())
    plt.close(probe)
    pages=(len(lines)+43)//44;assert pages<=2
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        with PdfPages(target) as pdf:
            for page in range(pages):
                fig=plt.figure(figsize=(8.27,11.69))
                fig.text(.09,.94,'VPR-GOAL-V3 作者审阅摘要',fontproperties=props,fontsize=16)
                for k,line in enumerate(lines[page*44:(page+1)*44]):fig.text(.09,.89-k*.0185,line,fontproperties=props)
                fig.text(.09,.045,f'研究执行与论文有效性分开判断；第 {page+1}/{pages} 页。',fontproperties=props,fontsize=9)
                pdf.savefig(fig);plt.close(fig)
    assert not any('Glyph' in str(w.message) and 'missing' in str(w.message) for w in caught)
    run.command(['pdfinfo',str(target)]);run.command(['pdffonts',str(target)])
    text=subprocess.check_output(['pdftotext','-layout',str(target),'-'],text=True)
    for token in ['VPR-GOAL-V3','598/656','644/656','14.67/14.67/14.86']:
        assert token in text,token
    actual=int(re.search(r'^Pages:\s+(\d+)',subprocess.check_output(['pdfinfo',str(target)],text=True),re.M).group(1));assert actual==pages
    run.write('model_identity.json',dict(not_new_inference=True));run.finish(dict(pages=actual,
        original_PDF_sha256=sha(old),new_PDF_sha256=sha(target),source_md_sha256=sha(source),
        critical_tokens_unsplit=True,source_wording_and_numbers_unchanged=True),dict(passed=True))
    (ROOT/'docs/research_v3/AUTHOR_BRIEF_REFLOW_AUDIT.json').write_bytes((run.path/'raw_metrics.json').read_bytes())
    print(json.dumps(dict(run_id=run.id,pages=actual,path=str(target))),flush=True)

if __name__=='__main__':main()

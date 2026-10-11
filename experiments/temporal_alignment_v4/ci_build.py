"""Exact-source PDF export on disposable public CI; never installs local TeX."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('GITHUB_REF')=='refs/heads/research/vpr-v4-temporal-alignment'
    out=ROOT/'paper/revisions/v4_build_receipts'/('run_'+os.environ['GITHUB_RUN_ID']+'_attempt_'+os.environ['GITHUB_RUN_ATTEMPT']);out.mkdir(parents=True,exist_ok=False);commands=[];versions={};failed=False
    def call(argv,cwd,name):
        start=datetime.now(timezone.utc).isoformat();p=subprocess.run(argv,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);(out/(name+'.stdout.txt')).write_text(p.stdout);(out/(name+'.stderr.txt')).write_text(p.stderr);commands.append(dict(argv=argv,cwd=str(cwd.relative_to(ROOT)),started_utc=start,ended_utc=datetime.now(timezone.utc).isoformat(),exit_code=p.returncode));return p
    for folder in sorted((ROOT/'paper/revisions').glob('v4_r[0-9][0-9]')):
        source=folder/'main.tex';pdf=folder/'main.pdf'
        # An existing PDF is reusable only with a retained exact-source receipt.
        # Earlier review bytes remain archived when a manuscript is corrected.
        existing_matches=False
        if pdf.exists():
            for old in (ROOT/'paper/revisions/v4_build_receipts').glob('*/receipt.json'):
                if old.parent==out:continue
                item=json.loads(old.read_text()).get('versions',{}).get(folder.name,{})
                if item.get('source_sha256')==sha(source) and item.get('pdf_sha256')==sha(pdf):
                    existing_matches=True;break
        if existing_matches:versions[folder.name]=dict(preserved_existing_PDF=True,pdf_sha256=sha(pdf),source_sha256=sha(source));continue
        ok=True
        for k in [1,2]:
            p=call(['pdflatex','-interaction=nonstopmode','-halt-on-error','-file-line-error','main.tex'],folder,folder.name+f'_pass{k}')
            if p.returncode:ok=False;failed=True;break
        receipt=dict(source_sha256=sha(source),compiled=ok)
        if (folder/'main.log').exists():(out/(folder.name+'.tex.txt')).write_bytes((folder/'main.log').read_bytes())
        if ok:
            info=call(['pdfinfo','main.pdf'],folder,folder.name+'_pdfinfo');fonts=call(['pdffonts','main.pdf'],folder,folder.name+'_pdffonts');call(['pdftotext','-layout','main.pdf',str(out/(folder.name+'.text.txt'))],folder,folder.name+'_pdftotext');log=(folder/'main.log').read_text();receipt.update(pdf_sha256=sha(pdf),pages=int(re.search(r'^Pages:\s+(\d+)',info.stdout,re.M).group(1)),unresolved_references=bool(re.search(r'(?:Citation .* undefined|Reference .* undefined|There were undefined references)',log)),overfull_boxes=re.findall(r'Overfull \\[hv]box[^\n]*',log),all_fonts_embedded=all(line.split()[-5]=='yes' for line in fonts.stdout.splitlines()[2:] if line.strip()))
            if receipt['pages']>6 or receipt['unresolved_references'] or not receipt['all_fonts_embedded']:failed=True
        versions[folder.name]=receipt
    (out/'receipt.json').write_text(json.dumps(dict(source_commit=os.environ['GITHUB_SHA'],versions=versions,passed=not failed,runner='standard ubuntu-24.04',old_V1_V3_files_untouched=True),indent=2)+'\n');(out/'commands.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in commands));print(json.dumps(versions,indent=2));return int(failed)
if __name__=='__main__':sys.exit(main())

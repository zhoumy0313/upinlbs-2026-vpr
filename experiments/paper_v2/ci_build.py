"""Build exact versioned manuscripts on CI only; preserve commands and PDF identities."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[2]
VERSIONS=['v2_r01','v2_r02','v2_r03','v2_empirical_findings','v2_r04']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    assert os.environ.get('GITHUB_ACTIONS')=='true', 'CI only; do not install TeX locally'
    assert os.environ.get('GITHUB_REF')=='refs/heads/research/temporal-vpr-v2'
    receipt=ROOT/'paper/revisions/ci_build_receipts'/('run_'+os.environ['GITHUB_RUN_ID']+'_attempt_'+os.environ['GITHUB_RUN_ATTEMPT'])
    receipt.mkdir(parents=True,exist_ok=False)
    records=[];failed=False
    def command(argv,cwd,name):
        started=datetime.now(timezone.utc).isoformat()
        p=subprocess.run(argv,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (receipt/(name+'.stdout.txt')).write_text(p.stdout);(receipt/(name+'.stderr.txt')).write_text(p.stderr)
        records.append(dict(argv=argv,cwd=str(cwd.relative_to(ROOT)),started_utc=started,ended_utc=datetime.now(timezone.utc).isoformat(),exit_code=p.returncode))
        return p
    result=dict(git_source_commit=os.environ['GITHUB_SHA'],run_id=os.environ['GITHUB_RUN_ID'],runner='standard ubuntu-24.04',versions={})
    result['pdflatex_version']=command(['pdflatex','--version'],ROOT,'tex_version').stdout.splitlines()[0]
    for version in VERSIONS:
        folder=ROOT/'paper/revisions'/version;pdf=folder/'main.pdf'
        if pdf.exists():
            result['versions'][version]=dict(preserved_existing_PDF=True,pdf_sha256=sha(pdf),source_sha256=sha(folder/'main.tex'))
            continue
        ok=True
        for attempt in [1,2]:
            p=command(['pdflatex','-interaction=nonstopmode','-halt-on-error','-file-line-error','main.tex'],folder,version+'_pass'+str(attempt))
            if p.returncode:ok=False;failed=True;break
        entry=dict(source_sha256=sha(folder/'main.tex'),compiled=ok)
        if (folder/'main.log').exists(): (receipt/(version+'.tex.txt')).write_bytes((folder/'main.log').read_bytes())
        if ok:
            info=command(['pdfinfo','main.pdf'],folder,version+'_pdfinfo')
            fonts=command(['pdffonts','main.pdf'],folder,version+'_pdffonts')
            command(['pdftotext','-layout','main.pdf',str(receipt/(version+'.text.txt'))],folder,version+'_pdftotext')
            entry.update(pdf_sha256=sha(pdf),pages=int(re.search(r'^Pages:\s+(\d+)',info.stdout,re.M).group(1)))
            entry['unresolved_references']=bool(re.search(r'(?:Citation .* undefined|Reference .* undefined|There were undefined references)',(folder/'main.log').read_text()))
            entry['overfull_boxes']=re.findall(r'Overfull \\[hv]box[^\n]*',(folder/'main.log').read_text())
            if entry['unresolved_references'] or (version in ['v2_r03','v2_r04','v2_empirical_findings'] and entry['pages']>6):failed=True
        result['versions'][version]=entry
    result['passed']=not failed
    (receipt/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    (receipt/'commands.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in records))
    print(json.dumps(result,indent=2))
    return int(failed)
if __name__=='__main__':sys.exit(main())

"""Final regression, V1 preservation, immutable freeze and exported PDF verification."""
import csv,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/temporal_vpr'))
from runtime import Run,digest,utc_now
VERSIONS=['v2_r01','v2_r02','v2_r03','v2_empirical_findings','v2_r04']
def main():
    run=Run(ROOT,'g5_delivery_verification',dict(versions=VERSIONS,no_new_research_evaluation=True),{})
    run.command([str(ROOT/'.venv-v2-smr/bin/python'),'-m','pytest','tests','experiments/temporal_vpr/tests','experiments/paper_v2/test_manuscript_audit.py','-q','--junitxml='+str(run.path/'regression.xml')],{'PYTHONPATH':'','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'})
    run.command([str(ROOT/'.venv-p0/bin/python'),'experiments/paper_v2/verify_manuscripts.py'])
    baseline=json.loads((ROOT/'docs/goals/v1_baseline_state.json').read_text())
    inventory=ROOT/baseline['full_inventory_path'];assert digest(inventory)==baseline['full_inventory_sha256']
    old=[]
    for row in json.loads(inventory.read_text()):
        p=ROOT/row['path'];assert p.exists(),row['path']
        if row['path']=='.gitignore':
            import hashlib
            actual=hashlib.sha256(p.read_bytes()[:row['bytes']]).hexdigest()
        else:actual=digest(p)
        assert actual==row['sha256'],row['path']
        old.append(dict(path=row['path'],sha256=actual,preserved=True))
    for name,expected in baseline['preserved_hashes'].items():assert digest(ROOT/name)==expected
    for ref in ['main','vpr-v1-frozen-20261010']:
        assert subprocess.check_output(['git','rev-parse',ref],cwd=ROOT,text=True).strip()==baseline['baseline_sha']
    freeze_name=json.loads((ROOT/'docs/goals/GOAL_V2_STATE.json').read_text())['freeze_directory']
    freeze=json.loads((ROOT/freeze_name/'freeze.json').read_text());frozen=[]
    for name,expected in freeze['file_sha256'].items():
        assert digest(ROOT/name)==expected,name;frozen.append(dict(path=name,sha256=expected,preserved=True))
    run.write('v1_preservation.json',dict(files=len(old),files_verified=old,exception='only append permitted after original .gitignore byte prefix'))
    run.write('freeze_preservation.json',dict(files=len(frozen),freeze_sha256=digest(ROOT/freeze_name/'freeze.json'),files_verified=frozen))
    receipts=[json.loads(p.read_text()) for p in sorted((ROOT/'paper/revisions/ci_build_receipts').glob('*/receipt.json'))]
    results=[]
    for version in VERSIONS:
        folder=ROOT/'paper/revisions'/version;pdf=folder/'main.pdf';source=folder/'main.tex'
        identity=next(r['versions'][version] for r in receipts if version in r['versions'] and r['versions'][version]['pdf_sha256']==digest(pdf))
        assert digest(source)==identity['source_sha256']
        # Each command is independently re-run locally against the exported exact-source PDF.
        run.command(['pdfinfo',str(pdf)])
        run.command(['pdffonts',str(pdf)])
        raw=run.path/(version+'.raw.txt');run.command(['pdftotext','-raw',str(pdf),str(raw)])
        layout=run.path/(version+'.layout.txt');run.command(['pdftotext','-layout',str(pdf),str(layout)])
        dest=run.path/'figures'/version;dest.mkdir(exist_ok=False)
        run.command(['pdftoppm','-png','-r','85',str(pdf),str(dest/'page')])
        info=subprocess.check_output(['pdfinfo',str(pdf)],text=True);fonts=subprocess.check_output(['pdffonts',str(pdf)],text=True)
        pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1));assert pages<=6
        font_rows=fonts.splitlines()[2:];assert font_rows and all('Type 3' not in row for row in font_rows)
        assert all(re.search(r'\s+yes\s+(?:yes|no)\s+(?:yes|no)\s+\d+\s+\d+\s*$',row) for row in font_rows)
        text=' '.join(raw.read_text().split());assert not re.search(r'\[\?\]|\?\?',text)
        ledger=json.loads((folder/'paper_numeric_evidence.json').read_text())['numeric_cells'];tex=source.read_text()
        table_rows=[]
        for table in re.findall(r'\\begin\{tabular\}.*?\\midrule(.*?)\\bottomrule',tex,re.S):
            for row in table.split(r'\\'):
                if '&' in row:
                    cells=[s.strip() for s in row.split('&')[1:]]
                    assert ' '.join(cells) in text,(version,cells,'PDF row mismatch')
                    table_rows.append(cells)
        abstract=[c for c in ledger if c['id'].startswith('abstract.') and c['correct'] is not None]
        assert all(c['display']+'%' in text for c in abstract)
        results.append(dict(revision=version,pages=pages,pdf_sha256=digest(pdf),tex_sha256=digest(source),font_count=len(font_rows),all_fonts_embedded=True,no_Type3=True,PDF_numeric_table_cells=sum(map(len,table_rows)),PDF_abstract_percentages=len(abstract),visual_inspection_pending=True))
    run.write('metrics.json',dict(results=results,old_files_verified=len(old),frozen_files_verified=len(frozen)))
    run.write('checks.json',dict(passed=True,regression_passed=True,V1_and_freeze_preserved=True,PDF_pages_fonts_numbers_verified=True,visual_checks_pending=True))
    with (run.path/'per_query.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=results[0].keys());w.writeheader();w.writerows(results)
    (run.path/'interpretation.md').write_text('All scientific inputs, old assets and frozen algorithms preserved; independent exported PDFs inspected numerically. Whole-page human/agent visual checks recorded separately after viewing. No experiment rerun for selection.\n')
    print(json.dumps(dict(run=run.id,results=results,old_files_verified=len(old),frozen_files_verified=len(frozen))),flush=True)
if __name__=='__main__':main()

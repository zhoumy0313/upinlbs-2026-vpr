"""Independent evidence audit and contiguous blocks, no online selection."""
import csv,json,re,subprocess
from pathlib import Path
import numpy as np
from .runtime import ROOT,Run,state,sha
from .evaluate import audit_csv

def main():
    st=state();run=Run('g6_numeric_PDF_audit','per-query/block/numeric binding and actual PDF checks',dict(frozen_parameters_unchanged=True));print(run.id,flush=True);g5=ROOT/'outputs_v3'/st['g5_run'];m=json.loads((g5/'raw_metrics.json').read_text());audit=audit_csv(g5/'per_query.csv',m['results']);blocks={};methodnames=set()
    with (g5/'per_query.csv').open() as f:
        for r in csv.DictReader(f):
            if r['common_valid']!='1':continue
            key=(r['method'],int(r['radius']),int(r['query_index'])//100);b=blocks.setdefault(key,dict(method=key[0],radius=key[1],block100=key[2],queries=0,correct=0,rescue=0,harm=0,net_vs_A=0));b['queries']+=1;b['correct']+=int(r['correct1']);b['rescue']+=int(r['rescue']);b['harm']+=int(r['harm']);b['net_vs_A']+=int(r['correct1'])-int(r['A_correct']);methodnames.add(r['method'])
    for r in m['results']:
        bs=[b for b in blocks.values() if b['method']==r['method'] and b['radius']==r['radius']];assert sum(b['net_vs_A'] for b in bs)==r['net'];assert sum(b['correct'] for b in bs)==r['correct']['1']
    with (run.path/'contiguous_blocks.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(next(iter(blocks.values()))));w.writeheader();w.writerows(blocks.values())
    reports=[]
    for folder in sorted((ROOT/'paper/revisions').glob('v3_r0[1-4]')):
        text=(folder/'main.tex').read_text();bindings=json.loads((folder/'numeric_bindings.json').read_text());assert '@@' not in text;assert not re.search(r'\\(?:input|include)\{',text);assert 'independent' in text.lower() and 'Acknowledgment' in text
        for b in bindings:
            assert sha(ROOT/b['file'])==b['sha256']
        cells=json.loads((folder/'table_cells.json').read_text())
        for cell in cells:assert cell['source_row'] in text
        # Poppler commands are read-only; native compiler/CI has already exported PDF.
        assert (folder/'main.pdf').exists();run.command(['pdfinfo',str(folder/'main.pdf')]);run.command(['pdffonts',str(folder/'main.pdf')]);target=run.path/(folder.name+'.text.txt');run.command(['pdftotext','-layout',str(folder/'main.pdf'),str(target)]);info=subprocess.check_output(['pdfinfo',str(folder/'main.pdf')],text=True);pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M).group(1));assert pages<=6
        extracted=target.read_text();assert 'Endpoint Drift' in extracted and 'Mingyang Zhou' in extracted
        for cell in cells:
            pattern=r'\s+'.join(re.escape(v) for v in cell['tokens']);assert re.search(pattern,extracted),cell
        reports.append(dict(revision=folder.name,pages=pages,source_sha256=sha(folder/'main.tex'),pdf_sha256=sha(folder/'main.pdf'),numeric_binding_sha256=sha(folder/'numeric_bindings.json'),all_table_counts_found_in_PDF=True,working_draft=True))
    run.write('model_identity.json',json.loads((ROOT/st['freeze_directory']/'model_identity.json').read_text()));run.finish(dict(numeric_audit=audit,papers=reports,blocks=len(blocks),methods=len(methodnames),no_IID_confidence_claim=True),dict(passed=True,PDF_page_limit_and_numeric_checks=True));(ROOT/'docs/research_v3/PDF_NUMERIC_AUDIT.json').write_bytes((run.path/'raw_metrics.json').read_bytes());(ROOT/'artifacts/v3/contiguous_blocks.csv').write_bytes((run.path/'contiguous_blocks.csv').read_bytes());state(g6_numeric_audit_run=run.id)
if __name__=='__main__':main()

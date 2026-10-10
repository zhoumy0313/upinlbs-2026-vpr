"""Independent ledger resolver and source-table audit; no manuscript-generator import."""
import argparse,csv,hashlib,json,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/temporal_vpr'))
from runtime import Run,digest

def evidence_bytes(path):
    p=ROOT/path
    if p.exists():return p.read_bytes()
    for archive in sorted((ROOT/'artifacts/v2').glob('*/evidence.zip')):
        with zipfile.ZipFile(archive) as z:
            if path in z.namelist():return z.read(path)
    raise FileNotFoundError(path)

def resolve(document,cell,role):
    if cell=='validation.common.R@1.queries':
        counts={r['common']['R@1']['queries'] for r in document['results'] if r['split']=='validation'}
        assert len(counts)==1
        return counts.pop()
    match=re.match(r'results\[([^\]]+)\]\.(.*)',cell)
    if match:
        selectors,tail=match.groups();parts=selectors.split(';');name=parts[0].split('=',1)[1]
        rows=[r for r in document['results'] if r['method']==name]
        if 'independent' in role and 'latency' not in role:
            radius=re.search(r'radius(?:_m=)?(\d+)',selectors)
            rows=[r for r in rows if r['radius_m']==(int(radius.group(1)) if radius else 25)]
        elif role=='development':rows=[r for r in rows if r['split']=='validation']
        assert len(rows)==1,(cell,role,len(rows))
        document=rows[0]
        if tail.startswith('R@'):tail='common.'+tail+'.correct'
        cell=tail
    match=re.match(r'trajectories\[role=([^\]]+)\]\.(.*)',cell)
    if match:
        key,cell=match.groups();document=next(r for r in document['trajectories'] if r['role']==key)
    for key in cell.split('.'):document=document[key]
    return document

def audit_revision(path):
    e=json.loads((path/'paper_numeric_evidence.json').read_text());tex=(path/'main.tex').read_text();documents={}
    verified=[]
    for cell in e['numeric_cells']:
        source=cell['source']
        if source not in documents:
            b=evidence_bytes(source);assert hashlib.sha256(b).hexdigest()==cell['source_sha256'];documents[source]=json.loads(b)
        actual=resolve(documents[source],cell['json_cell'],cell['role'])
        if cell['correct'] is not None:
            assert actual['correct']==cell['correct'] and actual['queries']==cell['queries']
            assert actual['queries']>0
            expected=100*actual['correct']/actual['queries']
        else:expected=actual
        assert abs(float(expected)-float(cell['value']))<1e-10,(cell['id'],expected,cell['value'])
        display=str(expected) if cell['format']=='literal' else format(float(expected),cell['format'])
        assert display==cell['display'],(cell['id'],display,cell['display'])
        assert display in re.sub(r'(?<=\d),(?=\d)', '', tex),(cell['id'],'missing from manuscript')
        verified.append(cell)
    # Independently parse every numeric data row in all four LaTeX tables.
    parsed=[]
    for table in re.findall(r'\\begin\{tabular\}.*?\\midrule(.*?)\\bottomrule',tex,re.S):
        for row in table.split(r'\\'):
            if '&' in row:
                fields=[s.strip() for s in row.split('&')[1:]]
                assert all(re.fullmatch(r'-?\d+(?:\.\d+)?',f) for f in fields),fields
                parsed.extend(fields)
    wanted=[c['display'] for c in verified if c['id'].startswith('table.')]
    assert sorted(parsed)==sorted(wanted),(len(parsed),len(wanted))
    cited=set(re.findall(r'\\cite\{([^}]+)\}',tex));bib=set(re.findall(r'\\bibitem\{([^}]+)\}',tex))
    assert cited<=bib and len(bib)==15
    refs=set(re.findall(r'\\(?:eq)?ref\{([^}]+)\}',tex));labels=set(re.findall(r'\\label\{([^}]+)\}',tex));assert refs<=labels
    assert e['outcome']=='C' and e['primary_protocol_outcome']=='B'
    assert '74.45' in tex and 'unsubstantiated' in tex and 'AI Disclosure' in tex and 'Additional authors and correspondence pending' in tex
    # Verify selected hard-coded experimental constants against frozen identities.
    freeze=json.loads((ROOT/e['freeze']/'freeze.json').read_text())
    heuristic=next(r for r in freeze['methods'] if r['name']=='adaptive_full')
    stats=heuristic['scales']
    assert stats['training_valid_queries']==592
    assert format(stats['A_gap_median'],'.8f')=='0.02154516'
    assert format(stats['T_gap_median'],'.8f')=='0.01837087'
    return dict(revision=path.name,numeric_cells=len(verified),numeric_table_cells=len(parsed),references=len(bib),source_sha256=digest(path/'main.tex'),passed=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',action='append');a=p.parse_args()
    versions=a.revision or ['v2_r01','v2_r02','v2_r03','v2_empirical_findings','v2_r04']
    run=Run(ROOT,'g5_independent_numeric_audit',dict(versions=versions,independent_of_generator=True),{})
    rows=[audit_revision(ROOT/'paper/revisions'/v) for v in versions]
    run.write('metrics.json',dict(results=rows,total_verified_numeric_cells=sum(r['numeric_cells'] for r in rows)))
    run.write('checks.json',dict(passed=True,raw_sources_SHA_verified=True,every_table_cell_parsed=True,all_reference_targets_defined=True))
    with (run.path/'per_query.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    (run.path/'interpretation.md').write_text('Independent raw-cell, numerator/denominator, display, table and citation audit. No method changes or test access for selection.\n')
    print(json.dumps(dict(run=run.id,results=rows)),flush=True)
if __name__=='__main__':main()

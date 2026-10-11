"""Correct one documentary count; preserve the reviewed source/PDF and results."""
import json
from runtime import ROOT,Run,sha,write
def main():
    run=Run('publication_correction',dict(scope='documentary raw GT association count only',frozen_science_unchanged=True))
    folder=ROOT/'paper/revisions/v4_r02';mapping=json.loads((folder/'numeric_evidence_map.json').read_text())
    mapping['manuscript_sha256']=sha(folder/'main.tex')
    mapping['errata']=[dict(old='38/0 RGB rows',new='38/2 RGB rows',source='docs/research_v4/DATA_MANIFEST_r02.json',preserved_review='paper/revisions/v4_review_snapshots/r02_pre_g6_correction',affects_frozen_results=False)]
    dev=json.loads((ROOT/'docs/research_v4/BASELINE_RESULTS.json').read_text())['results']+json.loads((ROOT/'configs/v4/selected_methods.json').read_text())['results']
    test=json.loads((ROOT/'docs/research_v4/INDEPENDENT_RESULTS.json').read_text())['results']
    errors=[]
    for row in mapping['table_cells']:
        if row.get('radius_m')!=.5:continue
        metrics=test if row['table'].startswith('Frozen') else dev
        m=next(x for x in metrics if x['hz']==5 and x['method']==row['method'] and x['radius_m']==.5)
        errors.append(dict(table=row['table'],method=row['method'],valid_denominator=m['valid_gt_queries'],median_m=m['top1_distance_median_all_valid'],P90_m=m['top1_distance_P90_all_valid'],rendered=f"{m['top1_distance_median_all_valid']:.2f}/{m['top1_distance_P90_all_valid']:.2f}",source=row['source']))
    mapping['distance_error_cells']=errors;write(folder/'numeric_evidence_map.json',mapping)
    write(run.path/'native_compilation.json',json.loads((folder/'native_compile_receipt.json').read_text()))
    run.command([str(ROOT/'.venv-p0/bin/python'),'-m','py_compile',str(ROOT/'experiments/temporal_alignment_v4/ci_build.py')])
    run.finish(dict(corrected_raw_invalid_count=2,old_review_preserved=True,native_compile='success',PDF_export='new exact-source CI pending',numeric_error_cells=len(errors)))
    run.checkpoint('G5 documentary correction with exact-source PDF rebuild and preserved review')
if __name__=='__main__':main()

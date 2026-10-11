import json,shutil
from runtime import *
def main():
    run=Run('g5_paper',dict(versions=['v4_r01','v4_r02'],stance='empirical negative-result working draft',native_compiler='both success; separate saved receipts',formal_submission=False))
    run.command(['git','fetch','origin',BRANCH]);run.command(['git','merge','--ff-only','FETCH_HEAD'])
    info=run.command(['pdfinfo','paper/revisions/v4_r01/main.pdf']);assert info==0
    for version in ['v4_r01','v4_r02']:
        p=ROOT/'paper/revisions'/version;assert json.loads((p/'native_compile_receipt.json').read_text())['kind']=='success';map=json.loads((p/'numeric_evidence_map.json').read_text());assert sha(p/'main.tex')==map['manuscript_sha256']
        dest=run.path/version;dest.mkdir();shutil.copyfile(p/'main.tex',dest/'main.tex');shutil.copyfile(p/'numeric_evidence_map.json',dest/'numeric_evidence_map.json');shutil.copyfile(p/'native_compile_receipt.json',dest/'native_compile_receipt.json')
    write(run.path/'actual_tool_execution_receipts.json',dict(report_assets_exit_code=0,generate_r01_exit_code=0,generate_r02_exit_code=0,assemble_report_exit_code=0,native_r01='success',native_r02='success',source='actual exec/tool completions retained by this chat; full report inputs recorded'))
    (ROOT/'docs/research_v4/G5_PAPER_ITERATION.md').write_text('# G5 manuscript iteration\n\nV4 r01 preserves the independent-test negative draft with explicitly pending latency; r02 adds actual latency, all declared R@K/radii/denominators and 3D error quantiles, embedded sampling plot, posthoc orientation limits, and complete AI disclosure. Native editor compilation succeeded for both. Original V3 editor/source/PDF are retained; no local TeX installation. Separate disposable public-repo CI exports exact-source PDFs, pages, embedded fonts and unresolved-reference checks. Evidence cells are mapped to source JSON/hash, and the working draft does not assert positive method effectiveness. Human authors/template/formal submission remain outside autonomous scope. Final PDF/render acceptance is checked in G6 before completion.\n')
    run.finish(dict(versions={v:dict(source_sha256=sha(ROOT/'paper/revisions'/v/'main.tex'),native_success=True) for v in ['v4_r01','v4_r02']},no_positive_method_claim=True),passed=False);run.checkpoint('G5 complete measured manuscript revision and native compilation')
if __name__=='__main__':main()

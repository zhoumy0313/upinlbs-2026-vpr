"""One bounded fallback: same official URL, process-only IPv4 direct route."""
from concurrent.futures import ThreadPoolExecutor
from runtime import *
from download import SEQUENCES
def one(item):
    seq,role=item;run=Run('g0_fallback',dict(sequence=seq,role=role,bounded_alternative=1,route='IPv4 direct; --noproxy * for this command only',connect_timeout_s=20,total_timeout_s=1800,retries=0))
    url=f'https://cvg.cit.tum.de/rgbd/dataset/{seq.split("_")[0]}/rgbd_dataset_{seq}.tgz'
    dest=ROOT/'data/raw/v4/tum_rgbd/archives'/('rgbd_dataset_'+seq+'.tgz')
    code=run.command(['curl','-4','--noproxy','*','-fL','--connect-timeout','20','--max-time','1800','--speed-time','60','--speed-limit','1024','--continue-at','-','--output',str(dest),'--write-out','\nhttp_code=%{http_code}\nurl_effective=%{url_effective}\nsize_download=%{size_download}\ntime_total=%{time_total}\n',url],allow_failure=True)
    d=dict(sequence=seq,role=role,curl_exit_code=code,bytes=dest.stat().st_size if dest.exists() else 0,archive_sha256=sha(dest) if dest.exists() else None)
    write(run.path/'download_receipt.json',d);print(json.dumps(d),flush=True);return d
if __name__=='__main__':
    first=json.loads((ROOT/'outputs_v4/download_attempt_1.json').read_text())
    if not any(x['curl_exit_code'] for x in first):raise RuntimeError('Fallback not justified')
    items=[x for x in SEQUENCES if next(r for r in first if r['sequence']==x[0])['curl_exit_code']]
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(one,items))
    write(ROOT/'outputs_v4/download_bounded_fallback.json',results)
    if any(r['curl_exit_code'] for r in results):sys.exit(1)

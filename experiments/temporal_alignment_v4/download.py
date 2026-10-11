"""Two official sources, resumable archives, no mirror/config mutation."""
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
from runtime import *
SEQUENCES=[('freiburg2_pioneer_slam','development'),('freiburg3_long_office_household','independent')]
def one(item):
    seq,role=item;run=Run('g0_download',dict(sequence=seq,role=role,retries=5,connect_timeout_s=20,total_timeout_s=1800))
    url=f'https://cvg.cit.tum.de/rgbd/dataset/{seq.split("_")[0]}/rgbd_dataset_{seq}.tgz'
    dest=ROOT/'data/raw/v4/tum_rgbd/archives'/('rgbd_dataset_'+seq+'.tgz')
    proxy={}
    for k in ['HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','https_proxy','http_proxy','all_proxy']:
        if os.environ.get(k):
            u=urlsplit(os.environ[k]);proxy[k]=dict(scheme=u.scheme,hostname=u.hostname,port=u.port,credentials_present=bool(u.username or u.password))
    write(run.path/'proxy_sanitized.json',proxy)
    argv=['curl','-fL','--retry','5','--retry-all-errors','--connect-timeout','20','--max-time','1800','--continue-at','-','--output',str(dest),'--write-out','\nhttp_code=%{http_code}\nurl_effective=%{url_effective}\nsize_download=%{size_download}\ntime_total=%{time_total}\n',url]
    code=run.command(argv,allow_failure=True)
    metrics=dict(sequence=seq,role=role,url=url,curl_exit_code=code,bytes=dest.stat().st_size if dest.exists() else 0,archive_sha256=sha(dest) if dest.exists() else None)
    write(run.path/'download_receipt.json',metrics)
    # Each worker saves independently, state/checkpoint performed by stage coordinator.
    print(json.dumps(metrics),flush=True)
    return metrics
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(one,SEQUENCES))
    write(ROOT/'outputs_v4/download_attempt_1.json',results)
    if any(r['curl_exit_code'] for r in results):sys.exit(1)

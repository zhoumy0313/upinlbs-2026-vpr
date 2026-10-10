"""Metadata only: bounded rsync listing and HEAD of the same-dataset tutorial mirror."""
from pathlib import Path
import shutil
import requests
from runtime import Run

def main():
    root=Path(__file__).resolve().parents[2]
    r=Run(root,'g1_independent_metadata',{'no_model_scores':True,'maximum_download_bytes':30_000_000_000,
        'datasets_probed':['St Lucia'],'stage':'G1 preliminary availability audit'}, {})
    print(r.id,flush=True)
    rsync=shutil.which('rsync')
    if rsync:
        code=r.command(['timeout','35s',rsync,'--list-only','--recursive','--timeout=20','--contimeout=15',
            'rsync://vandaldata.polito.it/sf_xl/VPR-datasets-downloader/st_lucia/'],allow_failure=True)
    else:code=None;r.event('rsync_unavailable',{'installed':False})
    try:
        response=requests.head('https://www.tu-chemnitz.de/etit/proaut/datasets/StLucia_small.zip',timeout=20,allow_redirects=True)
        head=dict(status_code=response.status_code,content_length=response.headers.get('Content-Length'),
            url=response.url,method='HEAD only, no dataset downloaded',
            provenance='same St Lucia dataset version used by original VPR_Tutorial loader, not a new alternate dataset')
    except requests.RequestException as e:head=dict(error_type=type(e).__name__)
    r.event('mirror_metadata_head',head)
    r.write('metrics.json',{'role':'network/size metadata only; no independent performance',
        'rsync_listing_exit_code':code,'same_dataset_mirror_head':head})
    r.write('checks.json',{'no_image_or_descriptor_download':True,'independent_performance_opened':False})
    (r.path/'per_query.csv').write_text('dataset,performance_opened\nStLucia,false\n')
    (r.path/'interpretation.md').write_text('Metadata discovery precedes freeze. A mirror version would require its own verified GT/order/licence protocol before evaluation. Listing failure is preserved and does not demonstrate that all sources are unavailable.\n')
    print(r.id,flush=True)

if __name__=='__main__':main()

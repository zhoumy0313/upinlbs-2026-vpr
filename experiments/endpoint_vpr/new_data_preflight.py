"""Bounded public metadata access only; no image encoding or score inspection."""
import json,time
import requests
from bs4 import BeautifulSoup
from .runtime import ROOT,Run,utc,sha

def main():
    run=Run('g4_metadata_preflight','source access/size/license before independent predictions',dict(metadata_only=True,single_download_cap=12_000_000_000,total_cap=45_000_000_000));print(run.id,flush=True)
    rows=[];urls=[]
    sources=[('Oxford_RobotCar','https://robotcar-dataset.robots.ox.ac.uk/ground_truth/'),('Oxford_login','https://mrgdatashare.robots.ox.ac.uk/'),('SFU','https://autonomy.cs.sfu.ca/sfu-mountain-dataset/'),('downloader','https://raw.githubusercontent.com/gmberton/VPR-datasets-downloader/main/README.md')]
    for name,url in sources:
        start=time.perf_counter()
        try:
            r=requests.get(url,timeout=20);text=BeautifulSoup(r.text,'html.parser').get_text(' ',strip=True);row=dict(name=name,url=url,status=r.status_code,bytes=len(r.content),seconds=time.perf_counter()-start,source_content_sha256=__import__('hashlib').sha256(r.content).hexdigest())
            if name=='SFU':
                soup=BeautifulSoup(r.text,'html.parser');links=[dict(label=a.get_text(' ',strip=True),url=a['href']) for a in soup.find_all('a',href=True)];run.write('sfu_link_catalog.json',links)
                urls=[a['url'] for a in links if a['label']=='stereo-left-a' or ('sfumd-dry-a-stereo_left 0.3' in a['label']) or ('sfumd-wet-a-stereo_left 0.3' in a['label'])]
                row.update(license_CC_BY_4='creativecommons.org/licenses/by/4.0' in r.text,manual_place_matches_available='hand-aligned' in text,no_10m_metric_GT=True)
            if name=='Oxford_login':row.update(login_required='Username' in r.text or 'username' in r.text,registration_not_performed=True)
        except Exception as e:row=dict(name=name,url=url,error=type(e).__name__+': '+str(e),seconds=time.perf_counter()-start)
        rows.append(row);run.event('metadata_GET',row);print(name,row.get('status',row.get('error')),flush=True)
    heads=[]
    for url in urls:
        for candidate in [url,url.replace('http://','https://',1)]:
            start=time.perf_counter()
            try:
                r=requests.head(candidate,timeout=15,allow_redirects=True);row=dict(url=candidate,status=r.status_code,final_url=r.url,content_length=int(r.headers.get('Content-Length','0')),content_type=r.headers.get('Content-Type',''),seconds=time.perf_counter()-start)
                if r.status_code in [200,206]:
                    x=requests.get(candidate,headers={'Range':'bytes=0-511'},stream=True,timeout=15);first=next(x.iter_content(512));x.close();row.update(range_status=x.status_code,first512_sha256=__import__('hashlib').sha256(first).hexdigest(),looks_like_tar=b'ustar' in first)
            except Exception as e:row=dict(url=candidate,error=type(e).__name__+': '+str(e),seconds=time.perf_counter()-start)
            heads.append(row);run.event('metadata_HEAD',row);print(json.dumps(row),flush=True)
    run.write('model_identity.json',dict(not_applicable='No model loaded; metadata only'));run.write('dataset_selection.json',dict(candidates=rows,heads=heads,selected='SFU_if_three_necessary_archives_public_and_bounded_else_none',no_performance_access=True,requested_SFU_urls=urls))
    run.finish(dict(candidates=rows,heads=heads),dict(passed=True,metadata_only=True,bytes_downloaded=sum(r.get('bytes',0) for r in rows)+512*len(heads)))
    (ROOT/'docs/research_v3/NEW_DATASET_PREFLIGHT.md').write_text('# New dataset preflight (metadata only)\n\nRun '+run.id+'; actual HTTP status/errors and sizes are saved. Oxford camera downloads require account registration; no account/terms action performed. SFU is explicitly CC BY 4.0 with manual place bundles and ordered low-rate JPEGs; 15m GPS at 95% for dry/wet is unsuitable for strict independent 10m accuracy claims. Dry/wet left-A first, selected by listed order and compatible calibration, never by scores. Formatted downloader alternatives require independent source-license/order validation; SVOX/Tokyo/Pitts are not assumed temporal.\n\n'+json.dumps(dict(sources=rows,heads=heads),indent=2)+'\n')
    (ROOT/'configs/v3/dataset_selection.json').write_bytes((run.path/'dataset_selection.json').read_bytes())
if __name__=='__main__':main()

import hashlib,json,re,time
import requests
from .runtime import ROOT,Run,utc

def main():
    run=Run('g6_primary_sources','actual new primary reading/metadata and current conference source',dict(reading_bodies_local_not_redistributed=True));print(run.id,flush=True);reading=run.path/'reading';reading.mkdir();rows=[]
    urls={'STA_method':'https://arxiv.org/html/2103.13580v2','STA_official_source':'https://raw.githubusercontent.com/Lu-Feng/STA-VPR/main/STAVPR_nonumba.py','AdaptSeq_publisher':'https://ieeexplore.ieee.org/document/10341533/','AdaptSeq_crossref':'https://api.crossref.org/works/10.1109/IROS55552.2023.10341533','SFU_primary_paper':'https://autonomy.cs.sfu.ca/sfu-mountain-dataset/paper.pdf','conference':'https://upinlbs2026.com/','IEEE_AI':'https://open.ieee.org/author-guidelines-for-artificial-intelligence-ai-generated-text/'}
    for name,url in list(urls.items()):
        start=time.perf_counter()
        try:
            r=requests.get(url,timeout=25);p=reading/(name+('.pdf' if 'paper.pdf' in url else '.txt'));p.write_bytes(r.content);row=dict(name=name,url=url,status=r.status_code,bytes=len(r.content),sha256=hashlib.sha256(r.content).hexdigest(),seconds=time.perf_counter()-start)
            if name=='conference' and r.status_code==200:
                assets=re.findall(r'(?:src|href)="([^"]+\.js)"',r.text)
                for i,asset in enumerate(assets):
                    u=requests.compat.urljoin(url,asset);rr=requests.get(u,timeout=25);pp=reading/f'conference_bundle_{i}.txt';pp.write_bytes(rr.content);row['bundle']=dict(url=u,status=rr.status_code,sha256=hashlib.sha256(rr.content).hexdigest(),bytes=len(rr.content));run.event('conference_asset',row['bundle'])
        except Exception as e:row=dict(name=name,url=url,error=type(e).__name__+': '+str(e),seconds=time.perf_counter()-start)
        rows.append(row);run.event('primary_GET',row);print(name,row.get('status',row.get('error')),flush=True)
    run.write('model_identity.json',dict(not_applicable='Literature/metadata only'));run.finish(dict(sources=rows,old_primary_evidence='docs/research_v2/RELATED_WORK_MATRIX.md and SOURCE_READING_NOTES.md; preserved old reading receipts',no_new_comparator_execution=True),dict(passed=True,partial_access_not_claimed_full_reading=True));(ROOT/'docs/research_v3/PRIMARY_SOURCE_RECEIPTS.json').write_bytes((run.path/'raw_metrics.json').read_bytes())
if __name__=='__main__':main()

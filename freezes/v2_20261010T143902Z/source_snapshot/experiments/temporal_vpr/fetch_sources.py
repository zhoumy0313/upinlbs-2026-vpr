"""Retain primary-source retrieval success/failures without treating titles as full text."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import requests
from runtime import Run,digest

class TextParser(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in {'script','style'}:self.skip+=1
    def handle_endtag(self,tag):
        if tag in {'script','style'}:self.skip=max(0,self.skip-1)
        if tag in {'p','div','section','h1','h2','h3','tr','li'}:self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--sources-config',type=Path)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    run=Run(root,'g1_primary_sources',{'primary_only':True,'purpose':'literature and independent metadata, no performance'}, {})
    print(run.id,flush=True)
    source_urls={
      'smr':'https://arxiv.org/html/2503.06840v2',
      'delta':'https://arxiv.org/html/2006.05700v2',
      'tomatch':'https://arxiv.org/html/2504.06116v2',
      'su':'https://arxiv.org/html/2510.13464v1',
      'rrf':'https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf',
      'seqslam':'https://www.cim.mcgill.ca/~dudek/417/Resources/seqslam-milford.pdf',
      'upinlbs_resnet_sinkhorn':'https://ieeexplore.ieee.org/document/11468446',
      'upinlbs_crossref':'https://api.crossref.org/works/10.1109/UPINLBS68186.2025.11468446',
      'downloader_readme':'https://raw.githubusercontent.com/gmberton/VPR-datasets-downloader/main/README.md',
      'downloader_api':'https://api.github.com/repos/gmberton/VPR-datasets-downloader/commits/main',
    }
    if args.sources_config:
        source_urls=json.loads(args.sources_config.read_text())
    receipts=[]
    for name,url in source_urls.items():
        start=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
        receipt=dict(name=name,url=url,started_utc=start,performance_read=False)
        try:
            response=requests.get(url,timeout=30)
            receipt.update(status_code=response.status_code,final_url=response.url,bytes=len(response.content),
                content_type=response.headers.get('Content-Type',''))
            raw=run.path/(name+('.pdf' if response.content.startswith(b'%PDF') else '.raw'))
            raw.write_bytes(response.content);receipt.update(path=str(raw.relative_to(root)),sha256=digest(raw))
            if response.status_code==200:
                if raw.suffix=='.pdf':
                    run.command(['pdftotext','-layout',str(raw),str(run.path/(name+'.txt'))])
                    receipt['access']='full PDF retrieved; reading required'
                else:
                    parser=TextParser();parser.feed(response.text)
                    (run.path/(name+'.txt')).write_text(''.join(parser.parts))
                    receipt['access']='retrieved; classify actual body before literature claim'
            else:receipt['access']='HTTP failure; not a full-text reading'
        except requests.RequestException as e:
            receipt.update(access='network failure',error_type=type(e).__name__,error=str(e).split('?')[0])
        receipt['ended_utc']=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
        run.event('http_get_receipt',receipt);receipts.append(receipt)
        print(json.dumps(receipt),flush=True)
    run.write('metrics.json',dict(role='source access, not VPR performance',receipts=receipts))
    run.write('checks.json',dict(all_attempts_retained=True,new_independent_performance_opened=False))
    run.write('source_receipts.json',receipts)
    (run.path/'per_query.csv').write_text('source_id,performance_read\n'+''.join(x+',false\n' for x in source_urls))
    (run.path/'interpretation.md').write_text('Raw articles and PDFs are local reading materials, excluded from public evidence redistribution. An HTTP 200 response is not evidence that the article body was read. HTTP failure/metadata-only access must be disclosed in the literature matrix. No independent scores computed.\n')

if __name__=='__main__':main()

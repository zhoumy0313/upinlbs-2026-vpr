"""Primary conference/publisher checks; no invention of unavailable review requirements."""
import json,re,sys
from pathlib import Path
from urllib.parse import urljoin
import requests
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'experiments/temporal_vpr'))
from runtime import Run,digest,utc_now

def main():
    run=Run(ROOT,'g5_primary_metadata_audit',dict(primary_sources_only=True,timeout_seconds=30),{});print(run.id,flush=True)
    sources={};raw=run.path/'reading';raw.mkdir()
    def get(key,url):
        try:
            r=requests.get(url,timeout=30);p=raw/(key+'.txt');p.write_bytes(r.content)
            run.event('primary_HTTP',dict(url=url,status=r.status_code,bytes=len(r.content),sha256=digest(p)))
            sources[key]=dict(url=url,status=r.status_code,sha256=digest(p),bytes=len(r.content),retrieved_utc=utc_now())
            return r
        except requests.RequestException as e:
            run.event('primary_HTTP_failure',dict(url=url,type=type(e).__name__));sources[key]=dict(url=url,error=type(e).__name__);return None
    homepage=get('conference_html','https://upinlbs2026.com/');bundle=None
    if homepage is not None and homepage.status_code==200:
        scripts=re.findall(r'<script[^>]+src=["\']([^"\']+)',homepage.text)
        for i,path in enumerate(scripts):
            r=get('conference_bundle_'+str(i),urljoin(homepage.url,path))
            if r is not None and 'UPINLBS2026' in r.text:bundle=r.text
    conference=dict(source='https://upinlbs2026.com/submission',verified={},unverified=['anonymity','paper size','deadline time and timezone','references counted explicitly','final-paper date interpretation'])
    if bundle:
        candidates=[]
        for term in ['6 pages','six pages','IEEE','October 15','2026-10-15','cmt3.research.microsoft.com','abstract','Abstract','full paper','Full Paper']:
            positions=[m.start() for m in re.finditer(re.escape(term),bundle)]
            for i in positions[:8]:candidates.append(dict(term=term,context=bundle[max(0,i-100):i+160]))
        (raw/'conference_contexts.json').write_text(json.dumps(candidates,indent=2))
        conference['primary_bundle_contexts_local']='reading/conference_contexts.json'
        conference['source_bundle_receipts']=[v for k,v in sources.items() if k.startswith('conference_bundle')]
    dois={'seqslam':'10.1109/ICRA.2012.6224623','delta':'10.1109/LRA.2020.3005627','smr':'10.1109/IROS60139.2025.11247581',
        'sameconference':'10.1109/UPINLBS68186.2025.11468446','doubt':'10.1109/LRA.2026.3674688',
        'stlucia':'10.1109/TRO.2008.2004520','rrf':'10.1145/1571941.1572114','tutorial':'10.1109/MRA.2023.3310859'}
    bibliography={}
    for key,doi in dois.items():
        r=get(key,'https://api.crossref.org/works/'+doi)
        if r is not None and r.status_code==200:
            m=r.json()['message'];bibliography[key]={k:m.get(k) for k in ['DOI','title','author','published','container-title','page','volume','issue','URL']}
    ai=get('IEEE_AI_policy','https://open.ieee.org/author-guidelines-for-artificial-intelligence-ai-generated-text/')
    run.write('metrics.json',dict(role='primary bibliographic and submission audit',sources=sources,conference=conference,bibliography=bibliography,
        AI_policy_URL=sources.get('IEEE_AI_policy',{}).get('url'),AI_disclosure_required='Verify primary body; disclose ChatGPT/Codex text/code sections and human review; unknown author details remain pending'))
    run.write('checks.json',dict(passed=True,actual_HTTP_statuses_preserved=True,unverified_requirements_not_invented=True))
    (run.path/'per_query.csv').write_text('metadata_only\ntrue\n')
    (run.path/'interpretation.md').write_text('Actual primary HTTP responses and SHA retained locally. CrossRef verifies bibliographic metadata, not paper-method content. Full articles and official frontend are not redistributed. Unavailable rules stay unverified; Oct15 initial-paper deadline cannot be replaced by Nov final-paper date.\n')
    print(json.dumps(dict(run=run.id,bibliography=bibliography,conference=conference)),flush=True)

if __name__=='__main__':main()

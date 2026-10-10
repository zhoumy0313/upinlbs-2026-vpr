import json,time,requests
from .runtime import ROOT,Run,utc

def main():
    cfg=json.loads((ROOT/'configs/v3/dataset_selection.json').read_text());run=Run('g4_public_GET_retry','bounded normal GET on official public links, no access-control bypass',dict(metadata_only=True,direct_client_disables_environment_proxy_only=True,does_not_change_system_or_Clash=True));print(run.id,flush=True);rows=[]
    for url in cfg['requested_SFU_urls']:
        for mode in ['standard','direct']:
            client=requests.Session();client.trust_env=mode=='standard';start=time.perf_counter()
            try:
                r=client.get(url,stream=True,timeout=(8,10));first=next(r.iter_content(512));r.close();row=dict(url=url,client=mode,status=r.status_code,content_length=r.headers.get('Content-Length'),first512_sha256=__import__('hashlib').sha256(first).hexdigest(),looks_like_tar=b'ustar' in first,seconds=time.perf_counter()-start)
            except Exception as e:row=dict(url=url,client=mode,error=type(e).__name__+': '+str(e),seconds=time.perf_counter()-start)
            rows.append(row);run.event('public_GET',row);print(json.dumps(row),flush=True)
    run.write('model_identity.json',dict(not_applicable='No encoder or images processed'));run.finish(dict(attempts=rows,no_independent_prediction=True),dict(passed=True,all_normal_access_attempts_retained=True));(ROOT/'docs/research_v3/NEW_DATASET_PREFLIGHT.md').open('a').write('\n## Bounded GET verification\n'+run.id+'\n'+json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()

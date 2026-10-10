"""Actual batch-one encodings and CPU/GPU scores; never a latency result."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image
import torch

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from vpr_research.artifacts import load_descriptors
from vpr_research.encoders.frozen import create_encoder
from causal import cosine_unit_scores,stable_ranking,stream_scores
from runtime import digest,atomic_json

def main():
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);args=p.parse_args()
    manifest=ROOT/'data/manifests/p1_20261010_132030_nordland_manifest_v2.json'
    lookup={r['image_id']:r for r in json.loads(manifest.read_text())['records']}
    cache=ROOT/'outputs/p3_eigenplaces_20261010_141736_ayAvV5/cosplace'
    gallery,gids,fp=load_descriptors(cache,manifest,'gallery')
    device='cuda' if torch.cuda.is_available() else 'cpu'
    encoder=create_encoder('cosplace',device,[224,224])
    assert encoder.fingerprint()['model_state_sha256']==fp['model']['model_state_sha256']
    tolerance=2e-5
    checks=[]
    for role in ['train','validation']:
        cached,ids,_=load_descriptors(cache,manifest,role)
        current=[]
        for i in range(9):
            path=ROOT/lookup[ids[i]]['relative_path'];assert digest(path)==lookup[ids[i]]['sha256']
            with Image.open(path) as im:current.append(encoder.encode([im]))
        real=np.concatenate(current)
        np.testing.assert_allclose(real,cached[:9],atol=tolerance,rtol=0)
        old_scores=cosine_unit_scores(cached[:9],gallery);real_scores=cosine_unit_scores(real,gallery)
        np.testing.assert_allclose(real_scores,old_scores,atol=tolerance,rtol=0)
        np.testing.assert_array_equal(stable_ranking(real_scores,10),stable_ranking(old_scores,10))
        np.testing.assert_array_equal(stable_ranking(stream_scores(real_scores,length=9),10),
            stable_ranking(stream_scores(old_scores,length=9),10))
        q=torch.tensor(real,dtype=torch.float64,device=device);g=torch.tensor(gallery,dtype=torch.float64,device=device)
        q=q/torch.linalg.vector_norm(q,dim=1,keepdim=True);g=g/torch.linalg.vector_norm(g,dim=1,keepdim=True)
        device_scores=(q@g.T).clamp(-1,1).cpu().numpy()
        np.testing.assert_allclose(device_scores,real_scores,atol=1e-12,rtol=0)
        np.testing.assert_array_equal(stable_ranking(device_scores,10),stable_ranking(real_scores,10))
        checks.append(dict(split=role,real_images=9,first9_stream_no_future=True,
            descriptor_atol=tolerance,score_atol=tolerance,cpu_gpu_float64_atol=1e-12,
            descriptor_max_abs_difference=float(np.max(abs(real-cached[:9]))),top10_equal=True,
            causal_temporal_top10_equal=True,not_latency_measurement=True))
    atomic_json(args.run_dir/'real_replay_checks.json',dict(passed=True,device=device,torch=torch.__version__,
        gpu=torch.cuda.get_device_name(0) if device=='cuda' else None,
        protocol='18 real development frames only; tolerance declared before replay',checks=checks))
    print(json.dumps(checks))

if __name__=='__main__':main()

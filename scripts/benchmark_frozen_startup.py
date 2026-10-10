#!/usr/bin/env python3
"""Separate warm-file model construction and gallery-index setup costs."""
import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'src'))
from frozen_package import digest,validate_package
from vpr_research.encoders.frozen import create_encoder
from vpr_research.retrieval import ExactCosineIndex


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--package',type=Path,required=True)
    args=p.parse_args();package=validate_package(args.package)
    acceptance=json.loads((args.run_dir/'phase_acceptance.json').read_text());assert acceptance['passed']
    device='cuda' if torch.cuda.is_available() else 'cpu';models={};indices={}
    def sync():
        if device=='cuda':torch.cuda.synchronize()
    for model in ['cosplace','eigenplaces','dinov2']:
        passes=[]
        for _ in range(3):
            sync();start=time.perf_counter()
            assert digest(ROOT/package['models'][model]['checkpoint'])==package['models'][model]['checkpoint_sha256']
            encoder=create_encoder(model,device);fp=encoder.fingerprint();sync()
            elapsed=time.perf_counter()-start
            assert fp['model_state_sha256']==package['model_state_sha256'][model]
            passes.append(elapsed);del encoder
            if device=='cuda':torch.cuda.empty_cache()
        models[model]={'warm_file_seconds_all_passes':passes,'mean_seconds':float(np.mean(passes)),
            'includes':'checkpoint SHA, frozen construction/strict loading, GPU transfer and full scientific fingerprint'}
        for dataset in ['nordland','gardens']:
            path=args.run_dir/'results'/dataset/model/'gallery_descriptors.npy'
            assert digest(path)==acceptance['source_sha256'][str(path.relative_to(args.run_dir))]
            arrays=np.load(path,allow_pickle=False);passes=[]
            for _ in range(3):
                start=time.perf_counter();index=ExactCosineIndex(arrays);passes.append(time.perf_counter()-start)
                size=index.database.nbytes;del index
            indices[dataset+'_'+model]={'warm_memory_seconds_all_passes':passes,'mean_seconds':float(np.mean(passes)),
                'index_bytes':size,'input_descriptor_bytes':arrays.nbytes,'source_sha256':digest(path),
                'includes':'float64 conversion and gallery L2 normalization; no disk read or query'}
    result={'scope':'Additional setup diagnostics; no final query or ground truth consumed',
        'device':device,'cold_machine_claim':False,'models':models,'indices':indices,
        'package_sha256':digest(args.package),'script_sha256':digest(Path(__file__))}
    with (args.run_dir/'startup_costs.json').open('x') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

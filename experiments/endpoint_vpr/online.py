"""Actual image pipeline; no query coordinates/GT/split/frame numbers in matching."""
import sys,time
import numpy as np
import torch
from PIL import Image
from .runtime import ROOT
from .baselines import Strategy
sys.path.insert(0,str(ROOT/'src'))
from vpr_research.encoders.frozen import create_encoder

def needed(spec):
    if spec['kind']=='single':return [spec['encoder']]
    if spec['kind'] in ['rrf','AB']:return ['cosplace','eigenplaces']
    return ['cosplace']

def sync():
    if torch.cuda.is_available():torch.cuda.synchronize()

class Online:
    def __init__(self,spec,traversals,galleries,encoders):
        self.matcher=Strategy(spec,traversals);self.galleries=galleries;self.encoders=encoders
    def reset(self):self.matcher.reset()
    def step(self,image_path):
        sync();start=time.perf_counter()
        with Image.open(image_path) as im:image=im.convert('RGB')
        decode_end=time.perf_counter();scores={};descriptors={};components=dict(decode=decode_end-start,preprocess=0.,encoding_transfer=0.,similarity=0.);previous=decode_end
        for name,encoder in self.encoders.items():
            prepared=encoder.prepare([image]);sync();prepared_end=time.perf_counter();desc=encoder.encode_tensor(prepared).cpu().numpy()[0];sync();encoded_end=time.perf_counter();unit=desc.astype(np.float64);unit/=np.linalg.norm(unit);scores[name]=np.clip(unit@self.galleries[name].T,-1,1);score_end=time.perf_counter();descriptors[name]=desc
            components['preprocess']+=prepared_end-previous;components['encoding_transfer']+=encoded_end-prepared_end;components['similarity']+=score_end-encoded_end;previous=score_end
        # Single B/DINO also supplies cosplace key as an unused aligned placeholder.
        if 'cosplace' not in scores:scores['cosplace']=next(iter(scores.values()))
        result,meta=self.matcher.step(scores);sync();end=time.perf_counter();components.update(history_ranking=end-previous,total=end-start)
        return result,meta,descriptors,scores,components

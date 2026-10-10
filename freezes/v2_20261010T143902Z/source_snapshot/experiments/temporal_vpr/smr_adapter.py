"""Execute fixed MIT source functions; disclose protocol adaptations explicitly."""
import ast
from collections import deque
from pathlib import Path
import subprocess
import numpy as np

SMR_COMMIT='82c88c90377110ce7a3340872f3e1179c3f2d396'

def official_functions(root,training=False):
    repository=Path(root)/'third_party/vpr-smr-predictor'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repository,text=True).strip()==SMR_COMMIT
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=repository,text=True).strip()
    env={'np':np}
    groups={'tools/mlp_classifier.py':['get_diagonals','extract_features_with_ranks'],
            'tools/data_processing.py':['max_normalise','transform_matrices','transform_matrices_with_window']}
    if training:
        import torch
        env['torch']=torch
        groups['tools/mlp_classifier.py']+=['generate_labels','mlp_train']
        groups['tools/data_processing.py']+=['compute_dist_matrix_seqslam']
    for filename,names in groups.items():
        parsed=ast.parse((repository/filename).read_text())
        functions=[node for node in parsed.body if isinstance(node,ast.FunctionDef) and node.name in names]
        assert {n.name for n in functions}==set(names)
        exec(compile(ast.Module(body=functions,type_ignores=[]),str(repository/filename),'exec'),env)
    return env

def official_window_features(history,functions):
    # Scores have no GT. Unit-descriptor squared L2 = 2 - 2*cosine.
    distances=(2-2*np.asarray(history,dtype=float)).T
    sample=functions['max_normalise'](distances)
    count=sample.shape[0]-sample.shape[1]+1
    if count<1:raise ValueError('Reference gallery shorter than sequence')
    empty=np.zeros((1,count)) # The returned SM transforms are unused by the feature function.
    block,_=functions['transform_matrices'](sample[None],empty)
    group,_=functions['transform_matrices_with_window'](sample[None],empty,window=2)
    return functions['extract_features_with_ranks'](sample,block[0],group[0],topN=1,epsilon=1e-6)[0]

class SmrMatcher:
    def __init__(self,root,pipeline,length=9):
        self.length=length;self.pipeline=pipeline;self.functions=official_functions(root);self.reset()

    def reset(self):self.history=deque(maxlen=self.length)

    def step(self,current_scores):
        s=np.asarray(current_scores,dtype=float)
        if s.ndim!=1 or not np.isfinite(s).all():raise ValueError('Finite cosine scores only')
        self.history.append(s.copy())
        if len(self.history)<self.length:
            return np.argsort(-s,kind='stable'),dict(warmup=True,abstained=False)
        h=np.stack(self.history);features=official_window_features(h,self.functions)
        probabilities=self.pipeline.predict_proba(features[None])[0]
        predicted=int(self.pipeline.classes_[np.argmax(probabilities)])
        # The official temporal convolution is a float32 sum over a unit diagonal.
        total=np.zeros(len(s)-self.length+1,dtype=np.float32)
        for lag in range(self.length):
            total += (2-2*h[-1-lag,self.length-1-lag:len(s)-lag]).astype(np.float32)
        endpoints=np.argsort(total,kind='stable')+self.length-1
        abstained=predicted in [1,3]
        rank=np.full(len(s),-1,dtype=int) if abstained else np.concatenate([endpoints,np.arange(self.length-1)])
        return rank,dict(warmup=False,abstained=abstained,predicted_class=predicted,
            confidence=float(np.max(probabilities)),official_ratios=features.tolist())

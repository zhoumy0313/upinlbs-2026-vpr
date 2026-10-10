"""Causal single-image A -> decision -> optional global B ranking replacement."""
from .core import ranking,score_features


class ConditionalRetriever:
    def __init__(self,a_encoder,a_index,b_encoder,b_index,policy):
        if a_index.database.shape[0]!=b_index.database.shape[0]:
            raise ValueError("A and B indices require the same ordered gallery")
        self.a_encoder,self.a_index=a_encoder,a_index
        self.b_encoder,self.b_index=b_encoder,b_index
        self.policy=policy
        self.a_calls=self.b_calls=0

    def infer(self,image):
        self.a_calls+=1
        a_descriptor=self.a_encoder.encode([image])
        a_scores=self.a_index.scores(a_descriptor)
        features=score_features(a_scores)
        gate_score,invoke=self.policy.decide(features)
        selected_scores=a_scores
        if bool(invoke[0]):
            # B has not been encoded or retrieved before the A-only decision.
            self.b_calls+=1
            b_descriptor=self.b_encoder.encode([image])
            selected_scores=self.b_index.scores(b_descriptor)
        return {"scores":selected_scores,"ranks":ranking(selected_scores,10),
                "invoked_B":bool(invoke[0]),"gate_score":float(gate_score[0])}

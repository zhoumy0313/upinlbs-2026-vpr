"""Exact cosine retrieval with gallery normalization paid at index creation."""
import numpy as np
from .core import l2_normalize, ranking


class ExactCosineIndex:
    def __init__(self, descriptors):
        self.database = l2_normalize(descriptors)

    def scores(self, query_descriptors):
        query = l2_normalize(query_descriptors)
        if query.shape[1] != self.database.shape[1]:
            raise ValueError("Query and gallery must use the same encoder")
        return np.clip(query @ self.database.T, -1, 1)

    def search(self, query_descriptors, k=10):
        scores = self.scores(query_descriptors)
        return scores, ranking(scores, k)

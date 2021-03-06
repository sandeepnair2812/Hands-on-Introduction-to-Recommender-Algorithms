"""
Utility functions
"""
__author__ = "Marcel Kurovski"
__copyright__ = "Marcel Kurovski"
__license__ = "mit"

import logging
import sys
from typing import Dict

import pandas as pd
import numpy as np
import scipy as sp


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


def get_entity_sim(a: int, b: int,
                   entity_ratings: Dict[int, float],
                   metric: str = 'pearson') -> tuple:
    """
    Cosine Similarity
    Pearson Correlation
    Adjusted Cosine Similarity
    Jaccard Similarity (intersection over union) - not a good idea as it does not incorporate ratings, e.g.
        even the same users have rated two items, highest Jaccard similarity as evidence for high item similarity,
        their judgement may be very differently on the two items, justifying dissimilarity
    """
    # 1. isolate e.g. users that have rated both items (a and b)
    key_intersection = set(entity_ratings[a].keys()).intersection(entity_ratings[b].keys())
    ratings = np.array([(entity_ratings[a][key], entity_ratings[b][key]) for key in key_intersection])
    n_joint_ratings = len(ratings)

    if n_joint_ratings > 1:
        # 2. apply a similarity computation technique
        if metric == 'pearson':
            # Warning and nan if for one entity the variance is 0
            sim = np.corrcoef(ratings, rowvar=False)[0, 1]
        elif metric == 'cosine':
            nom = ratings[:, 0].dot(ratings[:, 1])
            denom = np.linalg.norm(ratings[:, 0]) * np.linalg.norm(ratings[:, 1])
            sim = nom / denom
        elif metric == 'euclidean':
            sim = normalized_euclidean_sim(ratings[:, 0], ratings[:, 1])
        elif metric == 'adj_cosine':
            sim = None
        else:
            raise ValueError(f"Value {metric} for argument 'mode' not supported.")
    else:
        sim = None

    return sim, n_joint_ratings


def normalized_euclidean_sim(a, b):
    # scale to unit vectors
    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b)

    dist = np.linalg.norm(a_norm - b_norm)
    sim = 2 - dist - 1
    return sim


def min_max_scale(val, bounds):
    min_max_range = bounds['max']-bounds['min']
    return (val-bounds['min'])/min_max_range


def sigmoid(x):
    return 1/(1+np.exp(-x))


def df_to_coo(df, n_users, n_items):
    coo = sp.sparse.coo_matrix(([1]*len(df), (df.user.values-1, df.item.values-1)),
                               shape=(n_users, n_items), dtype=np.int32)
    return coo


def coo_to_df(coo):
    mat = np.concatenate((coo.row.reshape(-1, 1)+1,
                          coo.col.reshape(-1, 1)+1),
                         axis=1)
    return pd.DataFrame(mat, columns=['user', 'item'])


def get_sparsity(sparse_arr) -> float:
    num_elements = sparse_arr.shape[0]*sparse_arr.shape[1]
    num_nonzero_elements = sparse_arr.nnz
    density = num_nonzero_elements/num_elements
    return 1-density


def one_hot_encode_ids(ids: np.array, length):
    one_hot_enc = np.zeros((len(ids), length))
    one_hot_enc[np.arange(len(ids)), ids] = 1
    return one_hot_enc

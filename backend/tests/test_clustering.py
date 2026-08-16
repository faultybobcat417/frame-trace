import numpy as np

from frame_trace.clustering import DBSCANClusterEngine, pairwise_metrics
from frame_trace.demo import synthetic_vectors


def test_dbscan_clusters_demo_and_abstains():
    ids, vectors, _ = synthetic_vectors()
    result = DBSCANClusterEngine(eps=0.22, min_samples=2, membership_floor=0.72).fit(ids, vectors)
    assert len(result) == len(ids)
    assert sum(r.state == 'unassigned' for r in result) >= 2
    assert len({r.cluster_id for r in result if r.cluster_id is not None}) == 6


def test_pairwise_metrics_penalize_false_merge():
    truth = {'a':'x','b':'x','c':'y'}
    predicted = {'a':'z','b':'z','c':'z'}
    metrics = pairwise_metrics(truth, predicted)
    assert metrics['false_merge_pairs'] == 2
    assert metrics['pairwise_precision'] < 1

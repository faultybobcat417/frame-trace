import numpy as np

from frame_trace.clustering import ExactCosineIndex


def test_exact_cosine_search_orders_neighbors():
    index = ExactCosineIndex()
    index.add(['a','b'], np.array([[1,0],[0,1]], dtype=np.float32))
    result = index.search(np.array([0.9,0.1], dtype=np.float32), k=2)
    assert result[0][0] == 'a'
    assert result[0][1] > result[1][1]


def test_dimension_mismatch_rejected():
    index = ExactCosineIndex(np.array([[1,0]], dtype=np.float32), ['a'])
    try:
        index.add(['b'], np.array([[1,0,0]], dtype=np.float32))
    except ValueError as exc:
        assert 'dimension' in str(exc)
    else:
        raise AssertionError('expected ValueError')

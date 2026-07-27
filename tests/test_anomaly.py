import pytest
from services.anomaly import cosine_similarity


def test_cosine_similarity_identical():
    v = [1.0, 2.0, 3.0]
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_partial():
    a = [1.0, 2.0, 3.0]
    b = [1.0, 2.0, 3.1]
    score = cosine_similarity(a, b)
    assert 0.9 < score < 1.0


def test_cosine_similarity_zero_vector():
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == pytest.approx(0.0)

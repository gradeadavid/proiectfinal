import pytest

from embeddings_client import EmbeddingsClient


@pytest.fixture
def client():
    return EmbeddingsClient()


def test_cosine_similarity_identical_vectors(client):
    vec = [1.0, 2.0, 3.0]
    assert client.cosine_similarity(vec, vec) == pytest.approx(1.0)


def test_cosine_similarity_different_vectors(client):
    vec1 = [1.0, 0.0]
    vec2 = [1.0, 1.0]
    expected = 1 / (2 ** 0.5)
    assert client.cosine_similarity(vec1, vec2) == pytest.approx(expected)


def test_cosine_similarity_orthogonal_vectors(client):
    vec1 = [1.0, 0.0]
    vec2 = [0.0, 1.0]
    assert client.cosine_similarity(vec1, vec2) == pytest.approx(0.0)


def test_cosine_similarity_zero_vector(client):
    vec1 = [0.0, 0.0, 0.0]
    vec2 = [1.0, 2.0, 3.0]
    assert client.cosine_similarity(vec1, vec2) == 0.0

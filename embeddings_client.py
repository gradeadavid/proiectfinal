import requests

from config import EMBEDDINGS_MODEL, EMBEDDINGS_ENDPOINT
from embedding_generator import load_embeddings


class EmbeddingsClient:
    def get_embedding(self, text: str) -> list[float]:
        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                EMBEDDINGS_ENDPOINT,
                headers=headers,
                json={
                    "model": EMBEDDINGS_MODEL,
                    "prompt": text
                },
                timeout=15
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"Could not reach embeddings endpoint at "
                f"{EMBEDDINGS_ENDPOINT}: {e}"
            ) from e

        if not response.ok:
            print("STATUS:", response.status_code)
            print("BODY:", response.text)

        response.raise_for_status()
        data = response.json()
        # Ollama returns embedding directly
        if "embedding" in data:
            return data["embedding"]
        # Fallback for other formats
        return data["embeddings"][0]

    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a ** 2 for a in vec1) ** 0.5
        magnitude2 = sum(b ** 2 for b in vec2) ** 0.5
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def semantic_search(self, user_question: str,
                        top_k: int = 5, min_similarity: float = 0.5):
        question_embedding = self.get_embedding(user_question)
        embeddings_data = load_embeddings()

        scored = [
            {
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "similarity": self.cosine_similarity(
                    question_embedding, chunk["embedding"]
                ),
                "content": chunk["content"]
            }
            for chunk in embeddings_data
        ]
        scored.sort(key=lambda item: item["similarity"], reverse=True)

        return [item for item in scored if item["similarity"]
                >= min_similarity][:top_k]

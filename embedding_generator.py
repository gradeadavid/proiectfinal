"""Embeddings generation and caching module.

This module loads all document chunks and generates embeddings for each chunk.
Embeddings are cached in a JSON file. On each run, only documents that are new
or whose content changed since the last run are re-embedded; unchanged
documents reuse their cached embeddings.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict

from document_chunker import chunk_documents

logger = logging.getLogger(__name__)

EMBEDDINGS_FILE = Path(__file__).parent / "embeddings.json"


def _group_by_document(chunks: List[Dict]) -> Dict[str, List[Dict]]:
    grouped: Dict[str, List[Dict]] = {}
    for chunk in chunks:
        grouped.setdefault(chunk["document_id"], []).append(chunk)
    for doc_chunks in grouped.values():
        doc_chunks.sort(key=lambda c: c["chunk_index"])
    return grouped


def generate_and_save_embeddings() -> List[Dict]:
    """
    Generate embeddings for all chunks and save to JSON file, incrementally.

    Documents are re-chunked fresh from disk on every run. For each document,
    if its chunks are byte-identical to what's in the cached embeddings.json,
    the cached embeddings are reused (no API call). Otherwise (new or changed
    document) its chunks are re-embedded. Documents no longer present in the
    knowledge base are dropped from the result.

    Returns:
        List of dicts with structure:
        {
            "document_id": str,
            "chunk_index": int,
            "content": str,
            "embedding": list[float]
        }
    """
    from embeddings_client import EmbeddingsClient

    old_by_document = {}
    if EMBEDDINGS_FILE.exists():
        with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as f:
            old_by_document = _group_by_document(json.load(f))

    fresh_chunks = chunk_documents()
    if not fresh_chunks:
        logger.warning(
            "No chunks found. Please run the document chunking "
            "exercise first."
        )
        return []

    fresh_by_document = _group_by_document(fresh_chunks)

    embeddings_client = EmbeddingsClient()

    embeddings_data = []
    failed_chunks = []
    reused_count = 0
    regenerated_count = 0

    for document_id, new_chunks in fresh_by_document.items():
        old_chunks = old_by_document.get(document_id)
        old_contents = (
            [c["content"] for c in old_chunks] if old_chunks else None
        )
        new_contents = [c["content"] for c in new_chunks]
        unchanged = old_chunks is not None and old_contents == new_contents

        if unchanged:
            embeddings_data.extend(old_chunks)
            reused_count += len(old_chunks)
            continue

        logger.info(
            "Document '%s' is new or changed; (re)generating its embeddings.",
            document_id)
        for chunk in new_chunks:
            try:
                embedding = embeddings_client.get_embedding(chunk["content"])
                embeddings_data.append({
                    "document_id": chunk["document_id"],
                    "chunk_index": chunk["chunk_index"],
                    "content": chunk["content"],
                    "embedding": embedding
                })
                regenerated_count += 1
            except Exception:
                logger.warning(
                    "Error generating embedding for %s[%d]",
                    chunk["document_id"], chunk["chunk_index"], exc_info=True
                )
                failed_chunks.append(
                    (chunk["document_id"], chunk["chunk_index"]))

    if failed_chunks:
        logger.warning(
            "Failed to generate embeddings for %d chunk(s): %s",
            len(failed_chunks),
            failed_chunks)

    if not embeddings_data:
        logger.error("No embeddings were generated successfully.")
        raise RuntimeError(
            "Failed to generate any embeddings. "
            "Please check API configuration."
        )

    logger.info(
        "Saving %d embeddings to %s (%d reused, %d regenerated).",
        len(embeddings_data), EMBEDDINGS_FILE, reused_count, regenerated_count
    )
    with open(EMBEDDINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(embeddings_data, f, indent=2)

    return embeddings_data


def load_embeddings() -> List[Dict]:
    """
    Load embeddings from cached file.

    Returns:
        List of embedding dicts, or empty list if file doesn't exist.
    """
    if not EMBEDDINGS_FILE.exists():
        return []

    with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

from pathlib import Path
import json
from typing import List, Dict

from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_documents() -> List[Dict]:
    kb_root = Path(__file__).parent / "knowledge"
    result = []

    if CHUNK_SIZE <= 0:
        raise ValueError("CHUNK_SIZE must be > 0")
    if CHUNK_OVERLAP < 0 or CHUNK_OVERLAP >= CHUNK_SIZE:
        raise ValueError("CHUNK_OVERLAP must be >= 0 and < CHUNK_SIZE")
    step = CHUNK_SIZE - CHUNK_OVERLAP

    target_dirs = ["facts", "procedures", "prompts"]

    for sub in target_dirs:
        registry_path = kb_root / sub / "registry.json"
        docs = _load_registry(registry_path)
        for doc in docs:
            if doc.get("always_load", False):
                continue

            doc_id = doc.get("id")
            if not doc_id:
                continue

            content = _load_document(kb_root / sub, doc_id)
            if content is None:
                continue

            total = len(content)
            index = 0
            chunk_index = 0
            while index < total:
                chunk_text = content[index:index + CHUNK_SIZE]
                result.append({
                    "document_id": doc_id,
                    "chunk_index": chunk_index,
                    "content": chunk_text
                })
                chunk_index += 1
                index += step

    return result


def _load_registry(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _load_document(directory: Path, doc_id: str):
    doc_path = directory / f"{doc_id}.md"
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None

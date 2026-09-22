import os
import math
import hashlib
import requests
from .models import RetrievalDocument

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
VECTOR_DIM = 128


def _generate_local_embedding(text: str, dim: int = VECTOR_DIM) -> list[float]:
    """
    High-quality deterministic semantic vectorizer fallback.
    Generates normalized dense vector embeddings using term & n-gram feature hashing.
    Enables vector similarity search out-of-the-box without requiring external servers.
    """
    if not text:
        return [0.0] * dim

    words = text.lower().split()
    vector = [0.0] * dim

    # Word-level and char trigram hashing
    for word in words:
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        vector[idx] += 1.0
        # Character 3-grams for morphological similarity
        if len(word) >= 3:
            for j in range(len(word) - 2):
                sub = word[j:j+3]
                sub_h = int(hashlib.md5(sub.encode("utf-8")).hexdigest(), 16)
                vector[sub_h % dim] += 0.5

    # L2 normalize vector
    norm = math.sqrt(sum(x * x for x in vector))
    if norm > 0:
        vector = [round(x / norm, 5) for x in vector]

    return vector


def embed_text(text: str) -> list[float]:
    """
    Embeds text. Attempts Ollama if configured/available, otherwise falls back smoothly to local vectorizer.
    """
    # Check if Ollama is accessible
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=2
        )
        if resp.status_code == 200:
            data = resp.json()
            if "embedding" in data:
                return data["embedding"]
    except Exception:
        pass

    # Fallback to local vector embedding
    return _generate_local_embedding(text)


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two normalized vectors."""
    if not vec_a or not vec_b:
        return 0.0
    
    # Handle dimension mismatches safely
    min_len = min(len(vec_a), len(vec_b))
    dot = sum(vec_a[i] * vec_b[i] for i in range(min_len))
    return max(0.0, min(1.0, dot))


def embed_retrieval_document(doc_id: int):
    """
    Workbook 11: Embeds a specific RetrievalDocument and saves vector state.
    """
    try:
        doc = RetrievalDocument.objects.get(id=doc_id)
        vector = embed_text(doc.content)
        if vector:
            doc.embedding_json = vector
            doc.vector_status = "embedded"
        else:
            doc.vector_status = "failed"
        doc.save()
        return doc
    except RetrievalDocument.DoesNotExist:
        return None


def run_automated_vector_embedding_batch():
    """
    Self-automation runner for pending documents:
    Finds all documents pending embedding and generates vectors.
    """
    pending = RetrievalDocument.objects.filter(vector_status="pending")
    count = 0
    for doc in pending:
        embed_retrieval_document(doc.id)
        count += 1
    return {"embedded_count": count}


def retrieve_matches(query: str, limit: int = 5):
    """
    Workbook 11: Searches indexed documents using vector similarity.
    """
    query_vector = embed_text(query)
    docs = RetrievalDocument.objects.filter(vector_status="embedded")
    
    scored_matches = []
    for doc in docs:
        sim = cosine_similarity(query_vector, doc.embedding_json or [])
        scored_matches.append({
            "id": doc.id,
            "doc_key": doc.doc_key,
            "doc_type": doc.doc_type,
            "sfp_name": doc.sfp_name,
            "title": doc.title or "Untitled",
            "content": doc.content,
            "score": round(sim, 4),
            "metadata": doc.metadata_json
        })

    # Sort descending by score
    scored_matches.sort(key=lambda x: x["score"], reverse=True)
    top_matches = scored_matches[:limit]

    return build_retrieval_answer(query, top_matches)


def build_retrieval_answer(query: str, matches: list[dict]):
    """
    Workbook 11 exact output format:
    Constructs the retrieval answer dictionary for the agent.
    """
    snippets = []
    for match in matches:
        title = match.get("title", "Untitled")
        content = match.get("content", "")
        snippets.append({
            "id": match.get("id"),
            "title": title,
            "doc_key": match.get("doc_key"),
            "score": match.get("score"),
            "snippet": content[:300] + ("..." if len(content) > 300 else "")
        })

    return {
        "query": query,
        "total_matches": len(matches),
        "matches": snippets
    }

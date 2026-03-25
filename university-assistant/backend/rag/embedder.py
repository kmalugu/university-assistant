"""
Embedder Module
Handles text embedding using sentence-transformers (local) or Ollama.
"""
import logging
from typing import List

logger = logging.getLogger(__name__)

# Try to use sentence-transformers; fallback to simple hash-based mock for testing
try:
    from sentence_transformers import SentenceTransformer
    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    USE_SENTENCE_TRANSFORMERS = True
    logger.info("Using sentence-transformers for embeddings.")
except ImportError:
    USE_SENTENCE_TRANSFORMERS = False
    logger.warning("sentence-transformers not found. Using mock embeddings. Run: pip install sentence-transformers")


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of texts into vectors.

    Args:
        texts: List of strings to embed

    Returns:
        List of embedding vectors
    """
    if USE_SENTENCE_TRANSFORMERS:
        embeddings = _MODEL.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    else:
        # Mock embedding using character hashing (for testing only)
        import hashlib
        result = []
        for text in texts:
            h = hashlib.md5(text.encode()).hexdigest()
            vec = [int(h[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]  # 16-dim mock
            # Pad to 384 dims (MiniLM size)
            vec = (vec * 25)[:384]
            result.append(vec)
        return result


def embed_query(query: str) -> List[float]:
    """Embed a single query string."""
    return embed_texts([query])[0]

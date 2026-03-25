"""
RAG Retriever Module
Retrieves relevant documents for a given query and formats them for LLM context.
"""
import logging
from typing import List, Dict, Optional

from .vector_store import get_vector_store, initialize_vector_store

logger = logging.getLogger(__name__)


class UniversityRetriever:
    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self._initialized = False

    def _ensure_initialized(self):
        if not self._initialized:
            initialize_vector_store()
            self._initialized = True

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        doc_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        Retrieve top-k relevant documents for a query.

        Args:
            query: User query string
            top_k: Number of results (default: self.top_k)
            doc_type: Optional filter by document type

        Returns:
            List of document dicts with content, source, type, distance
        """
        self._ensure_initialized()
        store = get_vector_store()
        k = top_k or self.top_k
        results = store.query(query_text=query, n_results=k, filter_type=doc_type)
        return results

    def retrieve_with_scores(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve and include relevance scores (0-1, higher = more relevant)."""
        results = self.retrieve(query, top_k=top_k)
        for r in results:
            r["relevance_score"] = round(1 - r.get("distance", 0.5), 3)
        return results

    def format_context(self, query: str, top_k: int = 5) -> str:
        """
        Retrieve documents and format them as a context string for the LLM.

        Returns:
            Formatted context string
        """
        docs = self.retrieve(query, top_k=top_k)
        if not docs:
            return "No relevant university information found for this query."

        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.get("source", "university data")
            content = doc["content"].strip()
            context_parts.append(f"[Document {i} — Source: {source}]\n{content}")

        return "\n\n---\n\n".join(context_parts)

    def smart_retrieve(self, query: str, student_context: Dict = None) -> str:
        """
        Smart retrieval that adds student-context-aware filtering.

        Args:
            query: User query
            student_context: Dict with student info (program, year, nationality)

        Returns:
            Formatted context string
        """
        # Route query to appropriate doc types
        query_lower = query.lower()

        if any(w in query_lower for w in ["fee", "scholarship", "tuition", "payment", "hostel fee"]):
            doc_type = "fees"
        elif any(w in query_lower for w in ["course", "prerequisite", "credit", "syllabus", "elective"]):
            doc_type = "course"
        elif any(w in query_lower for w in ["deadline", "registration", "exam", "calendar", "holiday"]):
            doc_type = "calendar"
        elif any(w in query_lower for w in ["faculty", "professor", "teacher", "consultation"]):
            doc_type = "faculty"
        else:
            doc_type = None  # Search all

        # Enrich query with student context
        enriched_query = query
        if student_context:
            program = student_context.get("program", "")
            year = student_context.get("year", "")
            if program:
                enriched_query = f"{query} {program}"
            if year:
                enriched_query = f"{enriched_query} year {year}"

        return self.format_context(enriched_query, top_k=5)


# Singleton
_retriever_instance = None


def get_retriever() -> UniversityRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = UniversityRetriever()
    return _retriever_instance

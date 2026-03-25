"""
Vector Store Module
Manages ChromaDB collection for university documents.
Falls back to a simple in-memory TF-IDF store if ChromaDB is unavailable.
"""
import json
import logging
import os
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
CHROMA_PERSIST_DIR = Path(__file__).parent.parent.parent / "chroma_db"

# Try ChromaDB first
try:
    import chromadb
    from chromadb.config import Settings
    USE_CHROMA = True
except ImportError:
    USE_CHROMA = False
    logger.warning("ChromaDB not installed. Using in-memory fallback. Run: pip install chromadb")

# ===========================================================================
# Document loading helpers
# ===========================================================================

def load_text_documents() -> List[Dict]:
    """Load all text documents from the data directory."""
    docs = []
    for txt_file in DATA_DIR.rglob("*.txt"):
        with open(txt_file, "r", encoding="utf-8") as f:
            content = f.read()
        # Split by section
        sections = content.split("\n\n")
        for i, section in enumerate(sections):
            section = section.strip()
            if len(section) > 50:
                docs.append({
                    "id": f"{txt_file.stem}_{i}",
                    "content": section,
                    "source": str(txt_file.relative_to(DATA_DIR)),
                    "type": "policy",
                })
    return docs


def load_json_as_documents() -> List[Dict]:
    """Convert JSON data files into searchable text documents."""
    docs = []

    # Courses
    courses_path = DATA_DIR / "course_catalog" / "courses.json"
    if courses_path.exists():
        with open(courses_path) as f:
            data = json.load(f)
        for course in data.get("courses", []):
            prereqs = ", ".join(course.get("prerequisites", [])) or "None"
            syllabus = ", ".join(course.get("syllabus", []))
            text = (
                f"Course: {course['code']} - {course['title']}. "
                f"Credits: {course['credits']}. Department: {course['department']}. "
                f"Programs: {', '.join(course.get('programs', []))}. "
                f"Year: {course['year']}. "
                f"Prerequisites: {prereqs}. "
                f"Description: {course.get('description', '')}. "
                f"Syllabus topics: {syllabus}. "
                f"Lecture timings: {course.get('lecture_timings', 'TBA')}. "
                f"Faculty: {course.get('faculty', 'TBA')}."
            )
            docs.append({
                "id": f"course_{course['code']}",
                "content": text,
                "source": "course_catalog/courses.json",
                "type": "course",
                "metadata": {"code": course["code"], "department": course["department"]},
            })

    # Academic calendar
    cal_path = DATA_DIR / "academic_calendar" / "calendar.json"
    if cal_path.exists():
        with open(cal_path) as f:
            cal = json.load(f)
        for sem_key, sem in cal.get("semesters", {}).items():
            reg = sem.get("registration_window", {})
            text = (
                f"Academic calendar {cal['academic_year']} {sem['name']}. "
                f"Semester starts {sem['start']} and ends {sem['end']}. "
                f"Course registration opens {reg.get('start')} and closes {reg.get('end')}. "
                f"Late registration until {reg.get('late_registration_end')} with Rs. {reg.get('late_fee')} fine. "
                f"End semester exams from {sem['end_semester_exams']['start']} to {sem['end_semester_exams']['end']}. "
                f"Results declared on {sem['result_declaration']}."
            )
            docs.append({
                "id": f"calendar_{sem_key}",
                "content": text,
                "source": "academic_calendar/calendar.json",
                "type": "calendar",
            })

    # Fee structure
    fees_path = DATA_DIR / "fees" / "fee_structure.json"
    if fees_path.exists():
        with open(fees_path) as f:
            fees = json.load(f)
        for prog, pdata in fees.get("programs", {}).items():
            for nat in ["domestic", "international"]:
                if nat in pdata:
                    fd = pdata[nat]
                    text = (
                        f"Fee structure for {prog} program {nat} students. "
                        f"Tuition per semester: Rs. {fd.get('tuition_per_semester', fd.get('tuition_per_year', 'N/A'))}. "
                        f"Total per semester with hostel: Rs. {fd.get('total_per_semester_with_hostel', 'N/A')}. "
                        f"Payment deadline: {pdata.get('payment_deadline')}. "
                        f"Late fine: Rs. {pdata.get('late_fine_per_day')}/day."
                    )
                    docs.append({
                        "id": f"fees_{prog}_{nat}",
                        "content": text,
                        "source": "fees/fee_structure.json",
                        "type": "fees",
                    })
        for s in fees.get("scholarships", []):
            text = (
                f"Scholarship: {s['name']}. "
                f"Available for programs: {', '.join(s['programs'])}. "
                f"Eligibility: {s['eligibility']}. "
                f"Benefit: {s['benefit']}. "
                f"Renewal: {s['renewal']}. "
                f"Application deadline: {s['application_deadline']}."
            )
            docs.append({
                "id": f"scholarship_{s['name'].replace(' ', '_')}",
                "content": text,
                "source": "fees/fee_structure.json",
                "type": "scholarship",
            })

    # Faculty
    faculty_path = DATA_DIR / "faculty" / "faculty_directory.json"
    if faculty_path.exists():
        with open(faculty_path) as f:
            fac_data = json.load(f)
        for f in fac_data.get("faculty", []):
            text = (
                f"Faculty member: {f['name']}, {f['designation']} in {f['department']}. "
                f"Email: {f['email']}. Office: {f['office']}. "
                f"Consultation hours: {f['consultation_hours']}. "
                f"Specialization: {f.get('specialization', '')}. "
                f"Courses taught: {', '.join(f.get('courses', []))}."
            )
            docs.append({
                "id": f"faculty_{f['name'].replace(' ', '_')}",
                "content": text,
                "source": "faculty/faculty_directory.json",
                "type": "faculty",
            })

    return docs


# ===========================================================================
# ChromaDB Vector Store
# ===========================================================================

class ChromaVectorStore:
    def __init__(self, collection_name: str = "university_docs"):
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, documents: List[Dict]):
        ids = [d["id"] for d in documents]
        texts = [d["content"] for d in documents]
        metadatas = [
            {"source": d.get("source", ""), "type": d.get("type", "general")}
            for d in documents
        ]
        # Batch insert
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i:i+batch_size],
                documents=texts[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
            )
        logger.info(f"Added {len(documents)} documents to ChromaDB.")

    def query(self, query_text: str, n_results: int = 5, filter_type: str = None) -> List[Dict]:
        where = {"type": filter_type} if filter_type else None
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
        )
        docs = []
        for i, doc in enumerate(results["documents"][0]):
            docs.append({
                "content": doc,
                "source": results["metadatas"][0][i].get("source", ""),
                "type": results["metadatas"][0][i].get("type", ""),
                "distance": results["distances"][0][i] if results.get("distances") else 0,
            })
        return docs

    def count(self) -> int:
        return self.collection.count()


# ===========================================================================
# In-memory fallback (TF-IDF based)
# ===========================================================================

class InMemoryVectorStore:
    def __init__(self):
        self.documents: List[Dict] = []
        self._index = None

    def add_documents(self, documents: List[Dict]):
        self.documents.extend(documents)
        self._index = None  # Invalidate index
        logger.info(f"Added {len(documents)} documents to in-memory store.")

    def _build_index(self):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            self._vectorizer = TfidfVectorizer(stop_words="english")
            self._matrix = self._vectorizer.fit_transform([d["content"] for d in self.documents])
            self._cosine_sim = cosine_similarity
            self._np = np
            self._sklearn_available = True
        except ImportError:
            self._sklearn_available = False

    def query(self, query_text: str, n_results: int = 5, filter_type: str = None) -> List[Dict]:
        if self._index is None:
            self._build_index()

        docs = self.documents
        if filter_type:
            docs = [d for d in docs if d.get("type") == filter_type]

        if not docs:
            return []

        if getattr(self, "_sklearn_available", False):
            try:
                q_vec = self._vectorizer.transform([query_text])
                doc_matrix = self._vectorizer.transform([d["content"] for d in docs])
                scores = self._cosine_sim(q_vec, doc_matrix)[0]
                top_indices = self._np.argsort(scores)[::-1][:n_results]
                return [
                    {**docs[i], "distance": float(1 - scores[i])}
                    for i in top_indices if scores[i] > 0
                ]
            except Exception:
                pass

        # Keyword fallback
        q_words = set(query_text.lower().split())
        scored = []
        for doc in docs:
            content_words = set(doc["content"].lower().split())
            score = len(q_words & content_words) / max(len(q_words), 1)
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {**d, "distance": 1 - s}
            for s, d in scored[:n_results]
            if s > 0
        ]

    def count(self) -> int:
        return len(self.documents)


# ===========================================================================
# Factory
# ===========================================================================

_store_instance = None


def get_vector_store():
    """Get or create the vector store singleton."""
    global _store_instance
    if _store_instance is not None:
        return _store_instance

    if USE_CHROMA:
        _store_instance = ChromaVectorStore()
    else:
        _store_instance = InMemoryVectorStore()

    return _store_instance


def initialize_vector_store(force_reload: bool = False):
    """Load all documents into the vector store."""
    store = get_vector_store()

    if hasattr(store, "count") and store.count() > 0 and not force_reload:
        logger.info(f"Vector store already has {store.count()} documents. Skipping reload.")
        return store

    logger.info("Loading documents into vector store...")
    text_docs = load_text_documents()
    json_docs = load_json_as_documents()
    all_docs = text_docs + json_docs
    store.add_documents(all_docs)
    logger.info(f"Vector store initialized with {len(all_docs)} documents.")
    return store

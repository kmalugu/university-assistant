# University Student Information & Guidance Assistant

PROJECT 6 — AI-powered campus helpdesk with Ollama/Mistral, LangChain, RAG, FastAPI, Streamlit.

## Quick Start

1. Install: `pip install -r requirements.txt`
2. Start Ollama: `ollama serve` then `ollama pull mistral`
3. Start backend: `uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload`
4. Start frontend: `streamlit run frontend/app.py`
5. Open: http://localhost:8501

## Architecture
- Streamlit UI (7 tabs) → FastAPI (port 8000) → LLM (Ollama/Mistral) + RAG (ChromaDB) + 7 Tools
- Memory: Entity (student profile) + Conversation (multi-turn) + Persistent JSON sessions
- Cache: TTL-based (courses=24h, fees=7d, policies=30d)

## Tools Implemented (7)
1. Academic Calendar Tool (deadlines, exams, registration)
2. Course Lookup Tool (prereq checker, search)
3. Timetable Tool (weekly schedule by program/year)
4. Fee & Scholarship Tool (breakdown + eligibility)
5. Faculty Directory Tool (by department/name/course)
6. Campus Map Tool (buildings + walking directions)
7. Student Support Tool (hostel/library/medical/counseling)

## API Endpoints
POST /chat | GET /course/{code} | POST /timetable | POST /fees
POST /calendar | POST /rag | POST /faculty | GET /campus/{location}
GET /session/{id} | POST /session/{id}/update | DELETE /session/{id}

Full docs: http://localhost:8000/docs

## RAG Design Choice: ChromaDB over FAISS
ChromaDB chosen because:
- Persistent storage (survives restarts)
- Metadata filtering by doc_type
- Embedded mode (no external server)
Fallback: in-memory TF-IDF + cosine similarity if chromadb unavailable.

## Caching Strategy
| Data          | TTL    | Reason                         |
|---------------|--------|--------------------------------|
| Course catalog| 24h    | Fixed per semester             |
| Timetable     | 24h    | Fixed per semester             |
| Fee rules     | 7 days | Changed once per year          |
| Policies      | 30 days| Very stable                    |
| Calendar      | 1h     | Deadlines need freshness       |
| LLM responses | 5 min  | Identical repeated queries     |

## Evaluation Notebooks
- rag_eval.ipynb: Precision@5, Recall@5, Hit Rate
- bleu_rouge.ipynb: BLEU-1, BLEU-4, ROUGE-L, BERTScore
- latency_tests.ipynb: P95 latency, concurrent load (200 students)
- advising_quality_tests.ipynb: Relevance, Correctness, Personalization, Non-Hallucination, Policy Consistency

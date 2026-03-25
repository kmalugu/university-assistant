import os

from langchain_community.document_loaders import TextLoader, CSVLoader, JSONLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.rag.embedder import get_embedding_model
from langchain_core.documents import Document
import json
from pathlib import Path
from langchain_community.vectorstores import FAISS

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data"
FAISS_PATH = BASE_DIR / "faiss_index"


def load_documents():
    documents = []

    for root, dirs, files in os.walk(DATA_PATH):
        for file in files:
            file_path = os.path.join(root, file)

            if file.endswith(".txt"):
                loader = TextLoader(file_path)

            elif file.endswith(".csv"):
                loader = CSVLoader(file_path)

            elif file.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    for item in data:
                        if "question" in item and "answer" in item:
                            text = f"Q: {item['question']}\nA: {item['answer']}"
                        else:
                            text = ", ".join([f"{k}: {v}" for k, v in item.items()])

                        documents.append(
                            Document(page_content=text, metadata={"source": file_path})
                        )
                else:
                    text = ", ".join([f"{k}: {v}" for k, v in data.items()])

                    documents.append(
                        Document(
                            page_content=text,
                            metadata={"source": file_path}
                        )
                    )

            elif file.endswith(".pdf"):
                loader = PyPDFLoader(file_path)

            else:
                continue

            documents.extend(loader.load())

    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )
    return splitter.split_documents(documents)


def create_vector_store():
    docs = load_documents()
    chunks = split_documents(docs)

    embeddings = get_embedding_model()

    vectorstore = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )

    vectorstore.save_local(str(FAISS_PATH))
    return vectorstore


def load_vector_store():
    embeddings = get_embedding_model()

    return FAISS.load_local(
        str(FAISS_PATH),
        embeddings,
        allow_dangerous_deserialization=True
    )
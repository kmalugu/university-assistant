from backend.rag.vector_store import load_vector_store

def get_retriever():
    vectorstore = load_vector_store()

    return vectorstore.as_retriever(
        search_kwargs={"k" : 4}
    )
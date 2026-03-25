from backend.rag.rag_chain import rag_chain

if __name__ == "__main__":
    response = rag_chain.invoke("Who teaches machine learning?")
    print("\nRAG Response:\n", response)
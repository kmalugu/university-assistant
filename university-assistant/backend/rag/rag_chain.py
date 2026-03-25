from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from backend.rag.retriever import get_retriever
from backend.models.llm import llm

retriever = get_retriever()

# Prompt
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a university assistant. Answer only from the context."),
    ("user", "Question: {question}\n\nContext:\n{context}")
])

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# LCEL Rag Pipeline
rag_chain = (
    RunnableParallel({
    "context" : retriever | format_docs,
    "question" : RunnablePassthrough()
    })
    | rag_prompt
    | llm
    | StrOutputParser()
)

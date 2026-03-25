from fastapi import FastAPI
from pydantic import BaseModel
from .models.llm import chain
from backend.router import route_query
from backend.rag.rag_chain import rag_chain


app = FastAPI(title="University Assistant")


class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def root():
    return {"message": "University Assistant Backend Running"}


@app.post("/chat")
async def chat(request: ChatRequest):
    response = chain.invoke({
        "input" : request.message
    })
    return {"response": response}

@app.post("/assistant")
async def assistant(request: ChatRequest):
    result = route_query(request.message)
    return result

@app.post("/rag")
async def rag_query(request: ChatRequest):
    response = await rag_chain.ainvoke(request.message)
    return {"response": response}
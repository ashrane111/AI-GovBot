from fastapi import APIRouter, HTTPException
from models.model import Query, MessagesList, ResponseQuery
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from main.rag_pipeline import RAGPipeline
from langfuse.decorators import observe

answer_query_router = APIRouter()

@answer_query_router.post("/", response_model=ResponseQuery)
@observe()
async def answer_query(query_body: MessagesList):
    pipeline = RAGPipeline()
    messages_dicts = [{"role": msg.role, "content": msg.content} for msg in query_body.messages]
    try:
        answer, _ = await pipeline.run(messages_dicts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"res": "success", "answer": answer}
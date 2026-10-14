from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from mysite.chains.ai_search import ai_search

ai_router = APIRouter(prefix="/ai", tags=["AI Agent"])


class AISearchSchema(BaseModel):
    question: str = Field(min_length=2, max_length=2000)


@ai_router.post("/search")
def search_ai(data: AISearchSchema):
    try:
        return {"answer": ai_search(data.question)}
    except Exception:
        raise HTTPException(status_code=503, detail="Сервис AI Search временно недоступен.")

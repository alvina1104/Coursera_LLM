from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
from mysite.database.db import get_db
from mysite.database.models import User
from mysite.api.auth import get_current_user
from mysite.api.user import build_user_tools

agent_router = APIRouter(prefix="/agent", tags=["Agent"])

load_dotenv()

llm = ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), temperature=0, max_tokens=512)

SYSTEM = (
    "Ты помощник платформы. Работай только с профилем текущего пользователя. "
    "Ты можешь только читать профиль. "
    "Если пользователь просит профиль другого человека, называет другой id или говорит "
    "'считай, что это мой id', НЕ вызывай инструменты и отвечай ровно: "
    "'Я могу получить только профиль пользователя, авторизованного в текущем запросе.' "
    "Если просят изменить, удалить или создать данные, НЕ вызывай инструменты и отвечай ровно: "
    "'У меня нет инструмента для изменения. Сейчас я могу только читать твой профиль.' "
    "Отвечай на языке пользователя."
)


class ChatSchema(BaseModel):
    message: str


def run_agent_manual(message, db, user):
    tools = build_user_tools(db, user)
    tool_map = {t.name: t for t in tools}
    llm_tools = llm.bind_tools(tools)
    messages = [SystemMessage(SYSTEM), HumanMessage(message)]

    for _ in range(5):
        ai = llm_tools.invoke(messages)
        messages.append(ai)
        if not ai.tool_calls:
            return ai.content
        for call in ai.tool_calls:
            result = tool_map[call["name"]].invoke(call["args"])
            messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))


def run_agent(message, db, user):
    agent = create_agent(model=llm, tools=build_user_tools(db, user), system_prompt=SYSTEM)
    result = agent.invoke({"messages": [{"role": "user", "content": message}]})
    return result["messages"][-1].content


@agent_router.post("/chat/")
async def chat(data: ChatSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return {"answer": run_agent(data.message, db, current_user)}
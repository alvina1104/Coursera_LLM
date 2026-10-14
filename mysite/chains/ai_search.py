import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from mysite.base_knowledge.course_knowledge import search_courses, filter_courses, compare_courses, recommend_courses, list_courses
from langchain_core.runnables import RunnableLambda, RunnableParallel
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage

load_dotenv()


def format_courses(courses):
    if not courses:
        return "Подходящие курсы не найдены."
    return "\n".join(f"ID: {c.id} | {c.title} | Уровень: {', '.join(str(getattr(x, 'value', x)) for x in (c.level or []))} | Цена: {c.price} сом | Статус: {getattr(c.status, 'value', c.status)}" for c in courses)



@tool
def list_courses_tool() -> str:
    """Показывает все активные курсы."""
    return format_courses(list_courses())


@tool
def search_courses_tool(query: str) -> str:
    """Ищет курсы по названию или описанию."""
    return format_courses(search_courses(query))


@tool
def filter_courses_tool(level: str = "", status: str = "", max_price: int = 0) -> str:
    """Фильтрует курсы по уровню, статусу и максимальной цене."""
    return format_courses(filter_courses(level=level or None, status=status or None, max_price=max_price if max_price > 0 else None))


@tool
def compare_courses_tool(course_ids: list[int]) -> str:
    """Сравнивает курсы по их идентификаторам."""
    return format_courses(compare_courses(course_ids))


@tool
def recommend_courses_tool(level: str = "", max_price: int = 0) -> str:
    """Рекомендует курсы по уровню и бюджету."""
    return format_courses(recommend_courses(level=level or None, max_price=max_price if max_price > 0 else None))


tools = [list_courses_tool, search_courses_tool, filter_courses_tool, compare_courses_tool, recommend_courses_tool]
tools_by_name = {t.name: t for t in tools}

llm = ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), temperature=0.2, max_tokens=512).bind_tools(tools)

prompt = ChatPromptTemplate.from_messages([
    ("system", """Ты AI-помощник образовательной платформы.
Отвечай на языке клиента.
Выбирай только инструмент, подходящий к вопросу.
Не показывай все курсы, если клиент этого не просит.
Не выдумывай информацию о курсах.
Если данных недостаточно, уточни вопрос на языке клиента."""),
    ("human", "{question}")
])

input_chain = RunnableParallel(question=RunnableLambda(lambda d: d["question"].strip())) | prompt


def detect_intent(question: str) -> str:
    q = question.casefold()
    if any(w in q for w in ["все курсы", "все доступные курсы", "покажи все", "бардык курстар", "all courses"]): return "list"
    if any(w in q for w in ["сравни", "сравнение", "салыштыр", "compare"]): return "compare"
    if any(w in q for w in ["посоветуй", "рекомендуй", "предложи", "сунушта", "recommend"]): return "recommend"
    if any(w in q for w in ["до ", "не дороже", "дешевле", "баасы", "бюджет", "уровень", "деңгээл", "статус", "filter"]): return "filter"
    return "search"


def ai_search(question: str) -> str:
    if not question.strip(): return "Пожалуйста, введите вопрос."
    intent = detect_intent(question)
    if intent == "list": return list_courses_tool.invoke({})
    messages = input_chain.invoke({"question": question}).to_messages()
    if intent == "search":
        messages[0].content += "\nДля этого запроса используй только search_courses_tool."
    elif intent == "filter":
        messages[0].content += "\nДля этого запроса используй только filter_courses_tool."
    elif intent == "compare":
        messages[0].content += "\nДля этого запроса используй только compare_courses_tool."
    elif intent == "recommend":
        messages[0].content += "\nДля этого запроса используй только recommend_courses_tool."
    for _ in range(5):
        response = llm.invoke(messages)
        messages.append(response)
        if not response.tool_calls: return StrOutputParser().invoke(response)
        for call in response.tool_calls:
            try: result = tools_by_name[call["name"]].invoke(call["args"])
            except Exception as e:
                print(f"Ошибка инструмента {call['name']}: {e}")
                result = "Не удалось выполнить запрос. Попробуйте уточнить вопрос."
            messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
    return "Не удалось завершить запрос. Уточните вопрос."

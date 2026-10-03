from langchain_groq import ChatGroq

from backend.app.config import settings


def create_chat_model() -> ChatGroq:
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0,
    )


async def generate_research_response(brief: str) -> str:
    chat = create_chat_model()
    prompt = (
        "You are a market research assistant.\n"
        "Provide a short research response to the following brief.\n"
        "Do not invent facts.\n"
        "Keep the response concise.\n\n"
        f"Research brief: {brief}"
    )
    message = await chat.ainvoke(prompt)

    if isinstance(message.content, str):
        return message.content

    return "".join(
        block["text"]
        for block in message.content
        if isinstance(block, dict)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
    )
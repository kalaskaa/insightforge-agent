from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from backend.app.services.llm import create_chat_model
from backend.app.tools.company_profile import get_company_profile


MAX_ITERATIONS = 5


async def run_research_agent(brief: str) -> str:
    model = create_chat_model()
    model_with_tools = model.bind_tools([get_company_profile])

    messages = [
        SystemMessage(
            content=(
                "You are a market research assistant. "
                "Use the company profile tool when a brief asks for a supported "
                "company's profile. Give a concise final answer."
            )
        ),
        HumanMessage(content=brief),
    ]

    for _ in range(MAX_ITERATIONS):
        ai_message = await model_with_tools.ainvoke(messages)
        messages.append(ai_message)

        if not ai_message.tool_calls:
            if isinstance(ai_message.content, str):
                return ai_message.content

            return "".join(
                block["text"]
                for block in ai_message.content
                if isinstance(block, dict)
                and isinstance(block.get("text"), str)
            )

        for tool_call in ai_message.tool_calls:
            if tool_call["name"] == get_company_profile.name:
                tool_result = get_company_profile.invoke(tool_call["args"])
            else:
                tool_result = f"Tool {tool_call['name']} is not available."

            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call["id"],
                )
            )

    raise RuntimeError("Research agent reached the maximum number of iterations.")
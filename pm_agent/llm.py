"""LLM factory helpers."""

import os

from langchain_openai import ChatOpenAI

from pm_agent.config import load_settings


def get_llm() -> ChatOpenAI:
    """Create the DeepSeek chat model via its OpenAI-compatible API."""

    settings = load_settings()
    return ChatOpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", "0.2")),
    )


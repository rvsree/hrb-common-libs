"""Shared interface every LLM provider client implements (ask/ask_with_tools/
health_check) - ported unmodified from hrb_chatbot_v2's llm_client/base_llm_client.py."""

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Every provider client (OpenAI, Anthropic, OpenRouter) inherits from this."""

    PROVIDER_NAME = "base"
    ENV_KEY = ""

    @abstractmethod
    def ask(
        self,
        question: str,
        context: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def ask_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        tool_choice: str = "auto",
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> dict:
        raise NotImplementedError

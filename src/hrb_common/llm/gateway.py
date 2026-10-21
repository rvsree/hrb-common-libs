"""This extra's own gateway - deliberately scoped to llm providers only, unlike
hrb_chatbot_v2's combined ClientGateway (which also builds web/ci clients). That
combination is exactly the cross-extra coupling this package's extras design exists
to avoid - a service installing [llm] should never see web/ci imports at all."""

from hrb_common.llm.open_router_client import OpenRouterChatClient
from hrb_common.llm.openai_client import OpenAIChatClient, OpenAIEmbeddingClient


class LLMGateway:
    def __init__(self):
        self._openai_chat: OpenAIChatClient | None = None
        self._openai_embedding: OpenAIEmbeddingClient | None = None
        self._openrouter_chat: OpenRouterChatClient | None = None

    def openai_chat(self) -> OpenAIChatClient:
        if self._openai_chat is None:
            self._openai_chat = OpenAIChatClient()
        return self._openai_chat

    def openai_embedding(self) -> OpenAIEmbeddingClient:
        if self._openai_embedding is None:
            self._openai_embedding = OpenAIEmbeddingClient()
        return self._openai_embedding

    def openrouter_chat(self) -> OpenRouterChatClient:
        if self._openrouter_chat is None:
            self._openrouter_chat = OpenRouterChatClient()
        return self._openrouter_chat


_shared_gateway: LLMGateway | None = None


def get_llm_gateway() -> LLMGateway:
    global _shared_gateway
    if _shared_gateway is None:
        _shared_gateway = LLMGateway()
    return _shared_gateway


def reset_llm_gateway() -> None:
    global _shared_gateway
    _shared_gateway = None

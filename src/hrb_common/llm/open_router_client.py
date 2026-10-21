"""OpenRouter client - ported from hrb_chatbot_v2's llm_client/open_router_client.py,
import paths adjusted only."""

import requests
from openai import OpenAI

from hrb_common.llm.base_llm_client import BaseLLMClient
from hrb_common.observability.call_logger import log_backend_call
from hrb_common.observability.logger import get_logger
from hrb_common.observability.secrets import read_secret

logger = get_logger("openrouter_client")


class OpenRouterChatClient(BaseLLMClient):
    PROVIDER_NAME = "openrouter"
    ENV_KEY = "OPENROUTER_API_KEY"

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "openai/gpt-4.1-mini"
    HEALTH_CHECK_TIMEOUT_SECONDS = 10

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        site_url: str | None = None,
        site_name: str | None = None,
    ):
        self.api_key = read_secret("OPENROUTER_API_KEY", passed_in_value=api_key)
        self.model = read_secret("OPENROUTER_MODEL", self.DEFAULT_MODEL, passed_in_value=model)
        self.base_url = (read_secret("OPENROUTER_BASE_URL", self.DEFAULT_BASE_URL, passed_in_value=base_url) or "").rstrip("/")
        self.site_url = read_secret("OPENROUTER_SITE_URL", passed_in_value=site_url)
        self.site_name = read_secret("OPENROUTER_SITE_NAME", passed_in_value=site_name)

        if not self.api_key:
            logger.warning("[OPENROUTER] OPENROUTER_API_KEY not set")

        self.extra_headers = self.build_attribution_headers()

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.api_key else None

    def build_attribution_headers(self) -> dict:
        headers = {}
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            headers["X-Title"] = self.site_name
        return headers

    def get_client(self):
        if self.client is None:
            raise RuntimeError(f"{self.ENV_KEY} is not configured")
        return self.client

    def get_configuration(self) -> dict:
        return {"base_url": self.base_url, "model": self.model, "site_url": self.site_url, "site_name": self.site_name}

    def ask(self, question, context=None, system_prompt=None, temperature=0.0, max_tokens=None):
        message_text = f"Context:\n{context}\n\nQuestion:\n{question}" if context else question

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message_text})

        with log_backend_call(logger, "openrouter", "chat.ask", model=self.model, temperature=temperature):
            response = self.get_client().chat.completions.create(
                model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens,
                extra_headers=self.extra_headers or None,
            )

        answer = response.choices[0].message.content
        return answer if answer is not None else ""

    def ask_with_tools(self, messages, tools, temperature=0.0, max_tokens=None, tool_choice="auto"):
        with log_backend_call(logger, "openrouter", "chat.ask_with_tools", model=self.model, tool_count=len(tools)):
            response = self.get_client().chat.completions.create(
                model=self.model, messages=messages, tools=tools, tool_choice=tool_choice,
                temperature=temperature, max_tokens=max_tokens, extra_headers=self.extra_headers or None,
            )
        return response.model_dump()

    def health_check(self) -> dict:
        result = {"provider": self.PROVIDER_NAME}
        result.update(self.get_configuration())

        if not self.api_key:
            result["status"] = "unhealthy"
            result["message"] = "API key not configured"
            return result

        try:
            response = requests.get(
                self.base_url + "/key",
                headers={"Authorization": "Bearer " + self.api_key},
                timeout=self.HEALTH_CHECK_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            key_information = response.json().get("data", {})
            result["status"] = "healthy"
            result["key_label"] = key_information.get("label")
            result["usage"] = key_information.get("usage")
            result["limit"] = key_information.get("limit")
        except Exception as error:
            result["status"] = "unhealthy"
            result["message"] = str(error)

        return result

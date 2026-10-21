"""OpenAI clients: chat (+ tools) and embeddings - ported from hrb_chatbot_v2's
llm_client/openai_client.py, import paths adjusted only."""

from openai import OpenAI

from hrb_common.llm.base_llm_client import BaseLLMClient
from hrb_common.observability.call_logger import log_backend_call
from hrb_common.observability.logger import get_logger
from hrb_common.observability.secrets import read_secret

logger = get_logger("openai_client")

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


class OpenAIChatClient(BaseLLMClient):
    PROVIDER_NAME = "openai"
    ENV_KEY = "OPENAI_API_KEY"

    DEFAULT_BASE_URL = DEFAULT_OPENAI_BASE_URL
    DEFAULT_MODEL = "gpt-4.1-mini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        organization: str | None = None,
        project: str | None = None,
    ):
        self.api_key = read_secret("OPENAI_API_KEY", passed_in_value=api_key)
        self.model = read_secret("OPENAI_CHAT_MODEL", self.DEFAULT_MODEL, passed_in_value=model)
        self.base_url = (read_secret("OPENAI_BASE_URL", self.DEFAULT_BASE_URL, passed_in_value=base_url) or "").rstrip("/")
        self.organization = read_secret("OPENAI_ORG_ID", passed_in_value=organization)
        self.project = read_secret("OPENAI_PROJECT_ID", passed_in_value=project)

        if not self.api_key:
            logger.warning("[OPENAI] OPENAI_API_KEY not set")

        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key, base_url=self.base_url, organization=self.organization, project=self.project
            )
        else:
            self.client = None

        self.last_token_usage: dict | None = None

    def get_client(self):
        if self.client is None:
            raise RuntimeError(f"{self.ENV_KEY} is not configured")
        return self.client

    def get_configuration(self) -> dict:
        return {"base_url": self.base_url, "model": self.model, "organization": self.organization, "project": self.project}

    def ask(self, question, context=None, system_prompt=None, temperature=0.0, max_tokens=None, model_name_override=None):
        message_text = f"Context:\n{context}\n\nQuestion:\n{question}" if context else question

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message_text})

        resolved_model = model_name_override or self.model
        with log_backend_call(logger, "openai", "chat.ask", model=resolved_model, temperature=temperature):
            response = self.get_client().chat.completions.create(
                model=resolved_model, messages=messages, temperature=temperature, max_tokens=max_tokens
            )

        if response.usage:
            self.last_token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        else:
            self.last_token_usage = None

        answer = response.choices[0].message.content
        return answer if answer is not None else ""

    def ask_with_tools(self, messages, tools, temperature=0.0, max_tokens=None, tool_choice="auto"):
        with log_backend_call(logger, "openai", "chat.ask_with_tools", model=self.model, tool_count=len(tools)):
            response = self.get_client().chat.completions.create(
                model=self.model, messages=messages, tools=tools, tool_choice=tool_choice,
                temperature=temperature, max_tokens=max_tokens,
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
            model_list = list(self.get_client().models.list())
            result["status"] = "healthy"
            result["models_visible"] = len(model_list)
        except Exception as error:
            result["status"] = "unhealthy"
            result["message"] = str(error)

        return result


class OpenAIEmbeddingClient:
    PROVIDER_NAME = "openai_embedding"
    ENV_KEY = "OPENAI_API_KEY"

    DEFAULT_BASE_URL = DEFAULT_OPENAI_BASE_URL
    DEFAULT_MODEL = "text-embedding-3-small"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        organization: str | None = None,
        project: str | None = None,
    ):
        self.api_key = read_secret("OPENAI_API_KEY", passed_in_value=api_key)
        self.model = read_secret("OPENAI_EMBED_MODEL", self.DEFAULT_MODEL, passed_in_value=model)
        self.base_url = (read_secret("OPENAI_BASE_URL", self.DEFAULT_BASE_URL, passed_in_value=base_url) or "").rstrip("/")
        self.organization = read_secret("OPENAI_ORG_ID", passed_in_value=organization)
        self.project = read_secret("OPENAI_PROJECT_ID", passed_in_value=project)

        if not self.api_key:
            logger.warning("[OPENAI] OPENAI_API_KEY not set")

        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key, base_url=self.base_url, organization=self.organization, project=self.project
            )
        else:
            self.client = None

    def get_client(self):
        if self.client is None:
            raise RuntimeError(f"{self.ENV_KEY} is not configured")
        return self.client

    def get_configuration(self) -> dict:
        return {"base_url": self.base_url, "model": self.model, "organization": self.organization, "project": self.project}

    def get_embeddings(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        if not texts:
            return []

        resolved_model = model or self.model
        with log_backend_call(logger, "openai", "embeddings.create", model=resolved_model, text_count=len(texts)):
            response = self.get_client().embeddings.create(model=resolved_model, input=texts)

        return [item.embedding for item in response.data]

    def health_check(self) -> dict:
        result = {"provider": self.PROVIDER_NAME}
        result.update(self.get_configuration())

        if not self.api_key:
            result["status"] = "unhealthy"
            result["message"] = "API key not configured"
            return result

        try:
            available_model_names = [model.id for model in self.get_client().models.list()]
            result["status"] = "healthy"
            result["models_visible"] = len(available_model_names)
            result["embed_model_available"] = self.model in available_model_names
        except Exception as error:
            result["status"] = "unhealthy"
            result["message"] = str(error)

        return result

"""Tavily client - full port from hrb_chatbot_v2's web_client/tavily_client.py,
import paths adjusted only. Fully generic, no business logic."""

import time

import requests

from hrb_common.observability.logger import get_logger
from hrb_common.observability.secrets import read_secret

logger = get_logger("tavily_client")


class TavilyClient:
    PROVIDER_NAME = "tavily"
    ENV_KEY = "TAVILY_API_KEY"

    DEFAULT_BASE_URL = "https://api.tavily.com"
    DEFAULT_TIMEOUT_SECONDS = 30
    HEALTH_CHECK_TIMEOUT_SECONDS = 10
    MAX_SECONDS_BETWEEN_RETRIES = 10

    def __init__(self, api_key: str | None = None, base_url: str | None = None, project_id: str | None = None, timeout: int | None = None):
        self.api_key = read_secret("TAVILY_API_KEY", passed_in_value=api_key)
        self.base_url = (read_secret("TAVILY_BASE_URL", self.DEFAULT_BASE_URL, passed_in_value=base_url) or "").rstrip("/")
        self.project_id = read_secret("TAVILY_PROJECT_ID", passed_in_value=project_id)
        self.timeout = int(read_secret("TAVILY_TIMEOUT", str(self.DEFAULT_TIMEOUT_SECONDS), passed_in_value=str(timeout) if timeout else None))

        if not self.api_key:
            logger.warning("[TAVILY] TAVILY_API_KEY not set")

    def build_headers(self) -> dict:
        headers = {"Authorization": "Bearer " + str(self.api_key), "Content-Type": "application/json"}
        if self.project_id:
            headers["X-Project-ID"] = self.project_id
        return headers

    def get_configuration(self) -> dict:
        return {"base_url": self.base_url, "project_id": self.project_id, "timeout": self.timeout}

    def search(self, query: str, max_results: int = 5, search_depth: str = "basic", include_answer: bool = True, max_retries: int = 3) -> dict:
        if not self.api_key:
            return self.build_empty_result(query, "TAVILY_API_KEY not configured")
        if not query or not query.strip():
            return self.build_empty_result(query, "Query cannot be empty")

        request_body = {"query": query, "max_results": max_results, "search_depth": search_depth, "include_answer": include_answer}
        last_error = None

        for attempt_number in range(1, max_retries + 1):
            try:
                response = requests.post(self.base_url + "/search", json=request_body, headers=self.build_headers(), timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                return {"results": data.get("results", []), "answer": data.get("answer", ""), "query": query}
            except Exception as error:
                last_error = error
                logger.warning("[TAVILY] Attempt %d of %d failed: %s", attempt_number, max_retries, error)
                if attempt_number < max_retries:
                    time.sleep(min(2**attempt_number, self.MAX_SECONDS_BETWEEN_RETRIES))

        return self.build_empty_result(query, str(last_error))

    @staticmethod
    def build_empty_result(query: str, error_message: str) -> dict:
        return {"results": [], "answer": "", "query": query, "error": error_message}

    def health_check(self) -> dict:
        result = {"provider": self.PROVIDER_NAME}
        result.update(self.get_configuration())

        if not self.api_key:
            result["status"] = "unhealthy"
            result["message"] = "API key not configured"
            return result

        try:
            headers = self.build_headers()
            headers["Accept"] = "application/json"
            response = requests.get(self.base_url + "/usage", headers=headers, timeout=self.HEALTH_CHECK_TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            key_usage = data.get("key", {})
            account = data.get("account", {})
            result["status"] = "healthy"
            result["key_usage"] = key_usage.get("usage")
            result["key_limit"] = key_usage.get("limit")
            result["plan"] = account.get("current_plan")
        except Exception as error:
            result["status"] = "unhealthy"
            result["message"] = str(error)

        return result

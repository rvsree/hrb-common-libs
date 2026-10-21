from hrb_common.web.tavily_client import TavilyClient


def test_search_returns_error_result_without_api_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    client = TavilyClient()
    result = client.search("benefits question")
    assert result["results"] == []
    assert "TAVILY_API_KEY" in result["error"]


def test_search_returns_error_result_for_empty_query(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    client = TavilyClient()
    result = client.search("   ")
    assert result["error"] == "Query cannot be empty"


def test_health_check_reports_unhealthy_without_api_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    client = TavilyClient()
    assert client.health_check()["status"] == "unhealthy"


def test_build_headers_includes_project_id_when_configured(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    client = TavilyClient(project_id="proj-123")
    headers = client.build_headers()
    assert headers["X-Project-ID"] == "proj-123"

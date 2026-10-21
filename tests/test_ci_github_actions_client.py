from unittest.mock import MagicMock, patch

from hrb_common.ci.github_actions_client import GitHubActionsClient


def test_requires_explicit_repo_no_hardcoded_default():
    client = GitHubActionsClient(token="tok", repo="someorg/somerepo")
    assert client.repo == "someorg/somerepo"


def test_list_workflow_runs_returns_error_without_token():
    client = GitHubActionsClient(token="", repo="someorg/somerepo")
    result = client.list_workflow_runs("ci.yml")
    assert result["runs"] == []
    assert "token not configured" in result["error"]


def test_list_workflow_runs_parses_real_shape():
    fake_response = MagicMock()
    fake_response.json.return_value = {
        "total_count": 1,
        "workflow_runs": [{
            "id": 1, "run_number": 5, "status": "completed", "conclusion": "success",
            "head_sha": "abcdef1234567890", "html_url": "https://github.com/x", "created_at": "2026-01-01T00:00:00Z",
        }],
    }

    with patch("requests.get", return_value=fake_response):
        client = GitHubActionsClient(token="tok", repo="someorg/somerepo")
        result = client.list_workflow_runs("ci.yml")

    assert result["total_count"] == 1
    assert result["runs"][0]["head_sha"] == "abcdef1"


def test_health_check_reports_unhealthy_without_token():
    client = GitHubActionsClient(token="", repo="someorg/somerepo")
    assert client.health_check()["status"] == "unhealthy"

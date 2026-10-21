"""GitHub Actions REST client - ported from hrb_chatbot_v2's ci_client/github_actions_client.py.
Only change: no hardcoded default repo (the original defaults to "rvsree/hrb_chatbot_v2",
which has no meaning in a shared library) - callers must pass repo explicitly."""

import requests

from hrb_common.observability.logger import get_logger

logger = get_logger("github_actions_client")


class GitHubActionsClient:
    PROVIDER_NAME = "github_actions"
    ENV_KEY = "GITHUB_TOKEN"

    DEFAULT_BASE_URL = "https://api.github.com"
    DEFAULT_TIMEOUT_SECONDS = 15

    def __init__(self, token: str, repo: str, base_url: str | None = None):
        """repo: "owner/repo" - required, no default, since this is a shared library
        used across multiple repos, unlike hrb_chatbot_v2's own single-repo client."""
        self.token = token
        self.repo = repo
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")

        if not self.token:
            logger.warning("[GITHUB_ACTIONS] token not set")

    def build_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

    def list_workflow_runs(self, workflow_file: str, per_page: int = 5, page: int = 1) -> dict:
        if not self.token:
            return {"runs": [], "total_count": 0, "error": "token not configured"}

        url = f"{self.base_url}/repos/{self.repo}/actions/workflows/{workflow_file}/runs"
        try:
            response = requests.get(url, headers=self.build_headers(), params={"per_page": per_page, "page": page}, timeout=self.DEFAULT_TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
        except Exception as error:
            logger.warning("[GITHUB_ACTIONS] Could not list runs for %s: %s", workflow_file, error)
            return {"runs": [], "total_count": 0, "error": str(error)}

        runs = [
            {
                "id": run["id"], "run_number": run["run_number"], "status": run["status"], "conclusion": run["conclusion"],
                "head_sha": run["head_sha"][:7], "html_url": run["html_url"], "created_at": run["created_at"],
            }
            for run in data.get("workflow_runs", [])
        ]
        return {"runs": runs, "total_count": data.get("total_count", len(runs)), "error": None}

    def get_latest_run_sha_for_workflow(self, workflow_file: str) -> dict:
        if not self.token:
            return {"sha": None, "error": "token not configured"}

        url = f"{self.base_url}/repos/{self.repo}/actions/workflows/{workflow_file}/runs"
        try:
            response = requests.get(url, headers=self.build_headers(), params={"per_page": 1}, timeout=self.DEFAULT_TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
        except Exception as error:
            logger.warning("[GITHUB_ACTIONS] Could not fetch latest run for %s: %s", workflow_file, error)
            return {"sha": None, "error": str(error)}

        runs = data.get("workflow_runs", [])
        if not runs:
            return {"sha": None, "error": "No workflow runs found"}
        return {"sha": runs[0]["head_sha"], "error": None}

    def get_runs_for_sha(self, sha: str) -> dict:
        if not self.token:
            return {"runs": [], "error": "token not configured"}

        url = f"{self.base_url}/repos/{self.repo}/actions/runs"
        try:
            response = requests.get(url, headers=self.build_headers(), params={"head_sha": sha, "per_page": 10}, timeout=self.DEFAULT_TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
        except Exception as error:
            logger.warning("[GITHUB_ACTIONS] Could not list runs for sha %s: %s", sha, error)
            return {"runs": [], "error": str(error)}

        runs = [
            {
                "id": run["id"], "run_number": run["run_number"],
                "workflow_file": run["path"].rsplit("/", 1)[-1] if run.get("path") else run.get("name", ""),
                "status": run["status"], "conclusion": run["conclusion"], "html_url": run["html_url"], "created_at": run["created_at"],
            }
            for run in data.get("workflow_runs", [])
        ]
        return {"runs": runs, "error": None}

    def get_run_jobs(self, run_id: int) -> dict:
        if not self.token:
            return {"jobs": [], "error": "token not configured"}

        url = f"{self.base_url}/repos/{self.repo}/actions/runs/{run_id}/jobs"
        try:
            response = requests.get(url, headers=self.build_headers(), timeout=self.DEFAULT_TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
        except Exception as error:
            logger.warning("[GITHUB_ACTIONS] Could not list jobs for run %s: %s", run_id, error)
            return {"jobs": [], "error": str(error)}

        jobs = [
            {
                "name": job["name"], "status": job["status"], "conclusion": job["conclusion"], "html_url": job["html_url"],
                "steps": [
                    {"name": s["name"], "status": s["status"], "conclusion": s["conclusion"], "started_at": s.get("started_at"), "completed_at": s.get("completed_at")}
                    for s in job.get("steps", [])
                ],
            }
            for job in data.get("jobs", [])
        ]
        return {"jobs": jobs, "error": None}

    def health_check(self) -> dict:
        result = {"provider": self.PROVIDER_NAME, "repo": self.repo, "base_url": self.base_url}

        if not self.token:
            result["status"] = "unhealthy"
            result["message"] = "token not configured"
            return result

        try:
            response = requests.get(f"{self.base_url}/repos/{self.repo}", headers=self.build_headers(), timeout=self.DEFAULT_TIMEOUT_SECONDS)
            response.raise_for_status()
            result["status"] = "healthy"
        except Exception as error:
            result["status"] = "unhealthy"
            result["message"] = str(error)

        return result

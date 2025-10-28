from __future__ import annotations

from typing import Any

from dotenv import load_dotenv  # noqa: F401

from submission_analyzer.utils import get_json_with_retry

from .models import Code4renaIssue


class Code4renaAPI:
    baseUrl = "https://code4rena.com/api/v1"

    def __init__(self, contest_id: str, session_id: str | None):
        self.contest_id = contest_id
        if not session_id:
            raise ValueError("SESSION_CODE4 is not set")
        self.session_id = session_id

    def getAllSubmissions(self) -> list[Code4renaIssue]:
        page = 1
        perPage = 100
        total_submissions: list[Code4renaIssue] = []
        while True:
            resp = self._get_json(
                f"{self.baseUrl}/audits/{self.contest_id}/submissions?perPage={perPage}&page={page}"
            )
            submissions = resp.get("data", {}).get("submissions", [])
            for sub in submissions:
                total_submissions.append(Code4renaIssue.from_api(sub))
            page += 1
            if not resp.get("pagination", {}).get("nextPage"):
                return total_submissions

    def _get_json(self, url: str) -> dict[str, Any]:
        headers = {"Cookie": f"C4AUTH-LOGIN={self.session_id};"}
        return get_json_with_retry(url, headers=headers)

from __future__ import annotations

from typing import Any

from dotenv import load_dotenv  # noqa: F401

from submission_analyzer.utils import get_json_with_retry

from .models import Code4renaIssue
import requests as r


class Code4renaAPI:
    baseUrl = "https://code4rena.com/api/v1"

    def __init__(self, contest_id: str, username: str, password: str):
        self.contest_id = contest_id
        self.s = r.sessions.Session()
        self.login(username, password)

    def login(self, username, password) -> str:
        nonce = self._get_json(f"{self.baseUrl}/users/nonce?handle={username}")["nonce"]
        payload = {"nonce": nonce, "handle": username, "password": password}
        resp = self.s.post(f"{self.baseUrl}/users/session?type=password", payload)

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
        return get_json_with_retry(url, session=self.s)

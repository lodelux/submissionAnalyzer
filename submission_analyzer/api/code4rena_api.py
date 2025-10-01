from typing import Any

from submission_analyzer.models.code4rena_issue import Code4renaIssue
from submission_analyzer.utils import get_json_with_retry

import os
from dotenv import load_dotenv


class Code4renaAPI:
    baseUrl = "https://code4rena.com/api/v1"

    def __init__(self, contest_id, sessionId):
        self.contest_id = contest_id
        self.sessionId = sessionId

        if sessionId == None:
            raise ValueError("session id is not set in .env")
        self.sessionId = sessionId

    def getAllSubmissions(self):
        page = 1
        perPage = 100  # max allowed by code4rena
        total_submissions: list[Code4renaIssue] = []
        while True:
            resp = self._get_json(
                f"{self.baseUrl}/audits/{self.contest_id}/submissions?perPage={perPage}&page={page}"
            )
            submissions = resp.get("data").get("submissions")
            for sub in submissions:
                total_submissions.append(Code4renaIssue.from_api(sub))
            page += 1
            if not resp.get("pagination").get("nextPage"):
                return total_submissions
    


    def _get_json(self, url: str) -> dict[str, Any]:
        headers = {"Cookie": f"C4AUTH-LOGIN={self.sessionId};"}
        return get_json_with_retry(url, headers=headers)


if __name__ == "__main__":
    load_dotenv()

    contestId = "gtn2Umg6KsC"
    sessionId = os.getenv("SESSION_CODE4")

    c4api = Code4renaAPI(contestId, sessionId)

    submissions = c4api.getAllSubmissions()
    for sub in submissions:
        if sub.submitter_handle == "lodelux":
            print(sub)
        

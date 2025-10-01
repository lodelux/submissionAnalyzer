from submission_analyzer.utils import get_json_with_retry

class SherlockAPI:
    def __init__(self, contest_id, sessionId):
        self.contest_id = contest_id
        self.sessionId = sessionId

        if sessionId == None:
            raise ValueError("session id is not set in .env")
        self.sessionId = sessionId

    def getTitles(self):
        return self._get_json(
            f"https://audits.sherlock.xyz/api/contest/{self.contest_id}/issue_titles"
        )

    def getJudge(self):
        return self._get_json(
            f"https://audits.sherlock.xyz/api/judge/{self.contest_id}"
        )

    def getDiscussions(self, issueId):
        return self._get_json(
            f"https://audits.sherlock.xyz/api/issue/{issueId}/discussion"
        )

    def getContest(self):
        return self._get_json(
            f"https://audits.sherlock.xyz/api/contests/{self.contest_id}"
        )

    def _get_json(self, url):
        headers = {"Cookie": f"session={self.sessionId};"}
        return get_json_with_retry(url, headers=headers)

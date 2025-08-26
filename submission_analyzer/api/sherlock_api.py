import requests


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
        firstTimeout = 1
        attempts = 0
        MAX_ATTEMPTS = 15
        headers = {"Cookie": f"session={self.sessionId};"}
        resp = None
        while attempts < MAX_ATTEMPTS:
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                sleepTime = firstTimeout * (2 ** attempts)
                print(f"attempt {attempts}, retrying in {sleepTime}s")
                time.sleep(sleepTime)
                attempts += 1

            else:
                return resp.json()
        resp.raise_for_status()

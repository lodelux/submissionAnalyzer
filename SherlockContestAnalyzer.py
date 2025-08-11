#!/usr/bin/env python3
import argparse
import requests

severity_label = {1: "High", 2: "Medium"}

class SherlockAPI:
    def __init__(self, contest_id, sessionId):
        self.contest_id = contest_id
        self.sessionId = sessionId

    def getTitles(self):
        return self._get_json(f"https://audits.sherlock.xyz/api/contest/{self.contest_id}/issue_titles")
    
    def getJudge(self):
        return self._get_json(f"https://audits.sherlock.xyz/api/judge/{self.contest_id}")
    
    def getDiscussions(self, issueId):
        return self._get_json(f"https://audits.sherlock.xyz/api/issue/{issueId}/discussion")

    def _get_json(self, url):
        headers = {"Cookie", f"session={self.sessionId};"}
        resp = requests.get(url, headers)
        resp.raise_for_status()
        return resp.json()
    

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("totalPrizePool", type=int,  help="Total prize pool for the contest")
    parser.add_argument("contestId", type=int,  help="Contest ID")
    parser.add_argument("--issue-numbers", type=int, nargs="*", help="space-separated list of issue numbers")

    return parser.parse_args()

def main():

    args = parse_args()

    prizePool = args.totalPrizePool
    myIssuesNumbers = args.issue_numbers if args.issue_numbers != None else []

    sherlockAPI = SherlockAPI(args.contestId, "none")

    print(sherlockAPI.contest_id)


if __name__ == "__main__":
    main()
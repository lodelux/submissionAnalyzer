#!/usr/bin/env python3
import argparse
import requests
import os
from dotenv import load_dotenv


class SherlockAPI:
    def __init__(self, contest_id, sessionId):
        self.contest_id = contest_id
        self.sessionId = sessionId

        load_dotenv()
        sessionId = os.getenv("SESSION")
        if sessionId == None:
            raise ValueError("session id is not set in .env")
        self.sessionId = sessionId

    def getTitles(self):
        return self._get_json(f"https://audits.sherlock.xyz/api/contest/{self.contest_id}/issue_titles")
    
    def getJudge(self):
        return self._get_json(f"https://audits.sherlock.xyz/api/judge/{self.contest_id}")
    
    def getDiscussions(self, issueId):
        return self._get_json(f"https://audits.sherlock.xyz/api/issue/{issueId}/discussion")

    def _get_json(self, url):
        headers = {"Cookie": f"session={self.sessionId};"}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()

class Issue:
    def __init__(self, id: str = None, number: int = None, title: str = None):
        self.id = id
        self.number = number 
        self.title = title
        self.isSubmittedByUser = False
        self.isMain = False
        self.duplicateOf: Issue = None
        self.duplicates: list[Issue] = []
        self.comments = []
        self.severity = None
        self.points:float = 0
        self.reward:float = 0

def getValids(issues: list[Issue]):
    return [issue for issue in issues if issue.severity == 1 or issue.severity == 2]

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("totalPrizePool", type=int,  help="Total prize pool for the contest")
    parser.add_argument("contestId", type=int,  help="Contest ID")

    return parser.parse_args()

def addJudgingDetails(issues: dict[str, Issue], families):
    for family in families:
        mainDetails = family["main"]
        mainIssue =  issues[str(mainDetails["issue"])]
        familySeverity = family["primary_severity"]

        mainIssue.isSubmittedByUser = mainDetails["was_submitted_by_user"]
        mainIssue.isMain = True
        mainIssue.severity =  familySeverity

        for dupDetails in family["duplicates"]:
            dupIssue =  issues[str(dupDetails["issue"])]
            
            dupIssue.isSubmittedByUser = dupDetails["was_submitted_by_user"]
            dupIssue.duplicateOf = mainIssue
            dupIssue.severity = familySeverity

            mainIssue.duplicates.append(dupIssue)

def calculate_issue_points(submissions_count, severity):
    # severity: 1 = high, 2 = medium 3 = invalid
    base_points = 5 if severity == 1 else 1 if severity == 2 else 0
    return base_points * (0.9 ** (submissions_count - 1)) / submissions_count


def main():
    severity_label = {1: "High", 2: "Medium"}

    args = parse_args()

    prizePool = args.totalPrizePool
    totalPoints = 0

    sherlockAPI = SherlockAPI(args.contestId, "none")

    issues: dict[str, Issue] = {}

    
    for id,issue in sherlockAPI.getTitles().items():
        
        newIssue = Issue(id, issue["number"], issue["title"])

        if issues.get(id) != None:
            raise RuntimeError("issue Id was present already")
        
        issues[id] = newIssue

    # this directly modifies issues
    addJudgingDetails(issues, sherlockAPI.getJudge()[0]["families"])

    for issue in issues.values():
        if issue.isMain:
            # +1 to include main
            numberOfReports = 1 + len(issue.duplicates)
            pts = calculate_issue_points(numberOfReports, issue.severity)
            issue.points = pts
            totalPoints += pts * numberOfReports
            for dup in issue.duplicates:
                dup.points = pts
    
    for issue in issues.values():
        issue.reward = issue.points / totalPoints * prizePool

    print(f"my reward: {sum([issue.reward for issue in issues.values() if issue.isSubmittedByUser])}")
    print(f"issue breakdown for contest {args.contestId}:")
    for validIssue in sorted(getValids(issues.values()), key=(lambda i: i.reward), reverse=True):
        if not validIssue.isMain:
            continue
        print(f"{validIssue.number} - {validIssue.title} - {severity_label[validIssue.severity]} - {validIssue.reward:.2f} ({validIssue.points:.2f} points)")

    








        






    





if __name__ == "__main__":
    main()
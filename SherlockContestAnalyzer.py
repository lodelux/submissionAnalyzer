#!/usr/bin/env python3
import argparse
import requests
import os
from dotenv import load_dotenv


class SherlockAPI:
    def __init__(self, contest_id, sessionId):
        self.contest_id = contest_id
        self.sessionId = sessionId


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



def main():
    severity_label = {1: "High", 2: "Medium"}

    args = parse_args()

    prizePool = args.totalPrizePool
    totalPoints = 0
    issues: dict[str, Issue] = {}

    load_dotenv()
    sherlockAPI = SherlockAPI(args.contestId,os.getenv("SESSION") )


    for id,issue in sherlockAPI.getTitles().items():
        
        newIssue = Issue(id, issue["number"], issue["title"])

        if issues.get(id) != None:
            raise RuntimeError("issue was present already")
        
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

    visualizeIssues(severity_label, args.contestId, issues)


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


def truncate(text: str, max_len: int = 70) -> str:
    if text is None:
        return ""
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def yesno(flag: bool) -> str:
    return "Y" if flag else "N"


def visualizeIssues(severity_label, contestId, issues):
    my_total_reward = sum(issue.reward for issue in issues.values() if issue.isSubmittedByUser)

    # Build rows for valid main issues
    rows = []
    for validIssue in sorted(getValids(issues.values()), key=lambda i: i.reward, reverse=True):
        if not validIssue.isMain:
            continue
        dups = len(validIssue.duplicates)
        mine = validIssue.isSubmittedByUser or any(d.isSubmittedByUser for d in validIssue.duplicates)
        rows.append(
            (
                validIssue.number,
                truncate(validIssue.title, 70),
                severity_label.get(validIssue.severity, str(validIssue.severity)),
                dups,
                validIssue.points,
                validIssue.reward,
                mine,
            )
        )

    # Header
    print("\n=== Contest {} — Reward Breakdown ===".format(contestId))
    print("Your total expected reward: {:.2f}\n".format(my_total_reward))

    # Table header
    print(
        f"{'#':<5} {'Title':<70} {'Sev':<6} {'Dup':>3} {'Points':>10} {'Reward':>12} {'Mine':>5}"
    )
    print("-" * 115)

    # Table rows
    for num, title, sev, dup_count, pts, rew, mine in rows:
        print(
            f"{str(num):<5} {title:<70} {sev:<6} {dup_count:>3} {pts:>10.4f} {rew:>12.2f} {yesno(mine):>5}"
        )

    print("\nLegend: Dup = number of duplicates in family, Mine = Y if you submitted in this family.\n")

    








        






    





if __name__ == "__main__":
    main()
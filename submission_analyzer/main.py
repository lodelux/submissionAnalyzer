#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import asyncio

from submission_analyzer.api.sherlock_api import SherlockAPI
from submission_analyzer.models.sherlock_issue import Issue
from submission_analyzer.notifiers.telegram_notifier import TelegramBot
from submission_analyzer.utils import *
from submission_analyzer.io import cli

    


async def main():
    severity_label = {1: "High", 2: "Medium"}

    args = cli.parse_args()

    
    issues: dict[str, Issue] = {}

    load_dotenv()
    sherlockAPI = SherlockAPI(args.contestId, os.getenv("SESSION_SHERLOCK"))
    telegramBot = TelegramBot(os.getenv("BOT_TOKEN"), os.getenv("CHAT_ID"))

   
    while True:
        totalPoints = 0
        
        oldIssues = issues.copy()
        issues =  {}
        for id, issue in sherlockAPI.getTitles().items():

            newIssue = Issue(id, issue["number"], issue["title"])

            if issues.get(id) != None:
                raise RuntimeError("issue was present already")

            issues[id] = newIssue

        # this directly modifies issues
        addJudgingDetails(issues, sherlockAPI.getJudge()[0]["families"])

        if args.comments:
            addComments(issues, sherlockAPI)

        for issue in issues.values():
            if issue.isMain:
                # +1 to include main
                numberOfReports = 1 + len(issue.duplicates)
                pts = calculate_issue_points(numberOfReports, issue.severity)
                issue.points = pts
                totalPoints += pts * numberOfReports
                for dup in issue.duplicates:
                    dup.points = pts


        prizePool = sherlockAPI.getContest()["prize_pool"]

        for issue in issues.values():
            issue.reward = issue.points / totalPoints * prizePool

        if isIssuesMutated(oldIssues, issues):
            my_total_reward = sum(
                issue.reward for issue in issues.values() if issue.isSubmittedByUser
            )
            my_valid_issues = sum(
                1 for i in getValids(issues.values()) if i.isSubmittedByUser
            )
            my_total_issues = sum(
                1 for i in issues.values() if i.isSubmittedByUser
            )
            total_escalated = sum(1 for i in issues.values() if i.escalation["escalated"])
            total_resolved = sum(1 for i in issues.values() if i.escalation["resolved"])
            summary = (
                f"Reward: {my_total_reward:.2f} | "
                f"Valid issues: {my_valid_issues}/{my_total_issues} | "
                f"Escalations resolved: {total_resolved}/{total_escalated}"
            )
            await telegramBot.sendMessage(summary)
            cli.visualizeIssues(severity_label, args.contestId, issues, args)
        
        timeout = args.timeout
        if timeout == None:
            return
        await asyncio.sleep(args.timeout)









def addJudgingDetails(issues: dict[str, Issue], families):
    for family in families:
        mainDetails = family["main"]
        mainIssue = issues[str(mainDetails["issue"])]
        familySeverity = family["primary_severity"]

        mainIssue.isSubmittedByUser = mainDetails["was_submitted_by_user"]
        mainIssue.isMain = True
        mainIssue.severity = familySeverity
        mainIssue.escalation["escalated"] = mainDetails["has_escalation_comment"]
        mainIssue.escalation["resolved"] = mainDetails["escalation_resolved"]

        for dupDetails in family["duplicates"]:
            dupIssue = issues.get(str(dupDetails["issue"]))
            if not dupIssue:
                continue
            dupIssue.isSubmittedByUser = dupDetails["was_submitted_by_user"]
            dupIssue.duplicateOf = mainIssue
            dupIssue.severity = familySeverity
            dupIssue.escalation["escalated"] = dupDetails["has_escalation_comment"]
            dupIssue.escalation["resolved"] = dupDetails["escalation_resolved"]

            mainIssue.duplicates.append(dupIssue)


def addComments(issues: dict[str, Issue], sherlockAPI: SherlockAPI):
    count = 0
    total = len(issues.keys())
    for issue in issues.values():
        count += 1
        print(f"Fetching comments for issue {issue.number} - {count}/{total}", end="\r", flush=True )
        issue.comments = sorted(
            sherlockAPI.getDiscussions(issue.id)["comments"],
            key=lambda c: c.get("created_at"),
        )
    print()





def main_sync():
    asyncio.run(main())



if __name__ == "__main__":
    asyncio.run(main())

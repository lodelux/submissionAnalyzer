#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import traceback

from dotenv import load_dotenv

from submission_analyzer.monitoring import setup_sentry
from submission_analyzer.notifiers.telegram_notifier import TelegramBot
from .api import SherlockAPI
from .cli import parse_args, visualizeIssues
from .models import Issue
from .utils import calculate_issue_points, get_valids, is_issues_mutated


async def main():
    severity_label = {1: "High", 2: "Medium"}
    MAX_RETRIES = 5

    args = parse_args()

    issues: dict[str, Issue] = {}

    load_dotenv()
    setup_sentry()
    sherlockAPI = SherlockAPI(args.contestId, os.getenv("SESSION_SHERLOCK"))
    telegramBot = TelegramBot(os.getenv("BOT_TOKEN"), os.getenv("CHAT_ID"))

    retries = 0
    timeout = args.timeout
    sleep_on_error = timeout if timeout and timeout > 0 else 5

    while retries < MAX_RETRIES:
        try:
            totalPoints = 0

            oldIssues = issues.copy()
            issues = {}
            for id, issue in sherlockAPI.getTitles().items():

                newIssue = Issue(id, issue["number"], issue["title"])

                if issues.get(id) is not None:
                    raise RuntimeError("issue was present already")

                issues[id] = newIssue

            addJudgingDetails(issues, sherlockAPI.getJudge()[0]["families"])

            if args.comments:
                addComments(issues, sherlockAPI)

            for issue in issues.values():
                if issue.isMain:
                    numberOfReports = 1 + len(issue.duplicates)
                    pts = calculate_issue_points(numberOfReports, issue.severity)
                    issue.points = pts
                    totalPoints += pts * numberOfReports
                    for dup in issue.duplicates:
                        dup.points = pts

            prizePool = sherlockAPI.getContest()["prize_pool"]

            for issue in issues.values():
                issue.reward = (
                    issue.points / totalPoints * prizePool if totalPoints else 0
                )

            if is_issues_mutated(oldIssues, issues):
                my_total_reward = sum(
                    issue.reward for issue in issues.values() if issue.isSubmittedByUser
                )
                my_valid_issues = sum(
                    1 for i in get_valids(issues.values()) if i.isSubmittedByUser
                )
                my_total_issues = sum(1 for i in issues.values() if i.isSubmittedByUser)
                total_escalated = sum(
                    1 for i in issues.values() if i.escalation["escalated"]
                )
                total_resolved = sum(
                    1 for i in issues.values() if i.escalation["resolved"]
                )
                summary = (
                    f"Reward: {my_total_reward:.2f} | "
                    f"Valid issues: {my_valid_issues}/{my_total_issues} | "
                    f"Escalations resolved: {total_resolved}/{total_escalated}"
                )
                await telegramBot.sendMessage(summary)
                visualizeIssues(severity_label, args.contestId, issues, args)

            retries = 0
            if timeout is None:
                return
            await asyncio.sleep(timeout)
        except Exception as exc:
            retries += 1
            print(f"[sherlock] error while refreshing data: {exc}")
            traceback.print_exc()
            if retries >= MAX_RETRIES:
                raise RuntimeError("Exceeded maximum retries") from exc
            await asyncio.sleep(sleep_on_error)


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
        print(
            f"Fetching comments for issue {issue.number} - {count}/{total}",
            end="\r",
            flush=True,
        )
        issue.comments = sorted(
            sherlockAPI.getDiscussions(issue.id)["comments"],
            key=lambda c: c.get("created_at"),
        )
    print()


def main_sync():
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()

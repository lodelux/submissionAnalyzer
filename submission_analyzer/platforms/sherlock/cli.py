from __future__ import annotations

import argparse
from datetime import datetime

from submission_analyzer.utils import truncate, yesno

from .models import Issue
from .utils import get_invalids_escalated, get_valids


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "contestId",
        type=int,
        help="Contest ID, you can see it in the URL when you navigate to any Sherlock contest",
    )
    parser.add_argument(
        "-e", "--escalations", action="store_true", help="add escalations details"
    )
    parser.add_argument(
        "-c",
        "--comments",
        action="store_true",
        help="add comments details. Notice that with this flag active the script becomes extremely slow as it needs to query the API for each issue",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=None,
        help="How much time (in seconds) to sleep before running again. When omitted it runs once only",
    )
    return parser.parse_args()


def visualizeIssues(severity_label, contestId, issues: dict[str, Issue], args):
    my_total_reward = sum(
        issue.reward for issue in issues.values() if issue.isSubmittedByUser
    )

    total_escalated = sum(1 for i in issues.values() if i.escalation["escalated"])
    total_resolved = sum(
        1 for i in issues.values() if i.escalation["escalated"] and i.escalation["resolved"]
    )
    total_pending = total_escalated - total_resolved

    rows = []
    for validIssue in sorted(
        get_valids(issues.values()), key=lambda i: i.reward, reverse=True
    ):
        if not validIssue.isMain:
            continue
        dups = len(validIssue.duplicates)
        mine = validIssue.isSubmittedByUser or any(
            d.isSubmittedByUser for d in validIssue.duplicates
        )

        flattenedFamily = validIssue.duplicates.copy()
        flattenedFamily.append(validIssue)

        family_escalated = validIssue.escalation["escalated"] or any(
            d.escalation["escalated"] for d in validIssue.duplicates
        )
        if not family_escalated:
            family_resolved = False
        else:
            family_resolved = all(
                i.escalation["resolved"]
                for i in flattenedFamily
                if i.escalation["escalated"]
            )

        rows.append(
            (
                validIssue.number,
                truncate(validIssue.title, 70),
                severity_label.get(validIssue.severity, str(validIssue.severity)),
                dups,
                validIssue.points,
                validIssue.reward,
                mine,
                family_escalated,
                family_resolved,
            )
        )

    print(f"{datetime.now().strftime('%d/%m/%Y - %H:%M:%S')}\n=== Contest {contestId} — Breakdown   ===")
    totalIssues = len(issues)
    totalValids = len(get_valids(issues.values()))

    myTotalIssues = sum(1 for i in issues.values() if i.isSubmittedByUser)
    myValidIssues = sum(1 for i in get_valids(issues.values()) if i.isSubmittedByUser)

    print(
        f"Total issues: {totalIssues} - valid issues: {totalValids} - invalid issues: {totalIssues - totalValids} - your total issues: {myTotalIssues} - your valid issues: {myValidIssues} - your invalid issues: {myTotalIssues - myValidIssues} "
    )
    print("Your total expected reward: {:.2f}".format(my_total_reward))

    if args.comments:
        print(
            f"LJ commented on {sum(1 for i in issues.values() if i.severity == 3 and len(i.leadJudgeComments))} invalid issues"
        )

        lastComment = None
        lastIssue = None
        for issue in issues.values():
            for c in issue.leadJudgeComments:
                if lastComment is None or c["created_at"] > lastComment["created_at"]:
                    lastComment = c
                    lastIssue = issue

        if lastComment:
            print(
                f"LJ last commented at {datetime.fromtimestamp(lastComment['created_at']).strftime('%Y-%m-%d %H:%M:%S')} on issue {lastIssue.number}"
            )

    if args.escalations:
        print(
            "Escalations: {} escalated | {} resolved | {} pending\n".format(
                total_escalated, total_resolved, total_pending
            )
        )

    header = f"{'#':<5} {'Title':<73} {'Sev':<6} {'Dup':>3} {'Points':>10} {'Reward':>12} {'Mine':>5}"

    if args.escalations:
        header += f" {'Esc':>5} {'Res':>5}"

    print(header)
    print("-" * 140)

    for num, title, sev, dup_count, pts, rew, mine, esc, res in rows:
        row = f"{str(num):<5} {title:<73} {sev:<6} {dup_count:>3} {pts:>10.4f} {rew:>12.2f} {yesno(mine):>5}"
        if args.escalations:
            row += f" {yesno(esc):>5} {yesno(res):>5}"
        print(row)

    print("-" * 140)
    if args.escalations:
        print("\n=== Invalid issues (escalated) ===\n")
        header = f"{'#':<5} {'Title':<73} {'Dup':>3} {'Mine':>5} {'Esc':>5} {'Res':>5}"
        print(header)
        print("-" * 140)
        for invalidEscalatedIssue in sorted(
            get_invalids_escalated(issues.values()),
            key=lambda i: i.escalation["resolved"],
            reverse=True,
        ):
            print(
                f"{invalidEscalatedIssue.number:<5} {truncate(invalidEscalatedIssue.title, 73):<73} {len(invalidEscalatedIssue.duplicates):>3} {yesno(invalidEscalatedIssue.isSubmittedByUser):>5} {yesno(invalidEscalatedIssue.escalation['escalated']):>5} {yesno(invalidEscalatedIssue.escalation['resolved']):>5}"
            )

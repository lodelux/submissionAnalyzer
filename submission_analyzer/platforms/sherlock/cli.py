from __future__ import annotations

import argparse
from collections.abc import Iterable
from datetime import datetime
import sys

from submission_analyzer.utils import truncate, yesno

from .models import SherlockFinding, SherlockIssue, SherlockReport


def parse_sherlock_args():
    parser = argparse.ArgumentParser(
        prog="sherlock-analyzer",
        description="Analyze Sherlock contest submissions and estimate HM rewards.",
    )
    parser.add_argument(
        "contestId",
        type=int,
        help="Contest ID (visible in the URL when viewing a Sherlock contest).",
    )
    parser.add_argument(
        "-e",
        "--escalations",
        action="store_true",
        help="Include escalation columns in the report output.",
    )
    parser.add_argument(
        "-c",
        "--comments",
        action="store_true",
        help=(
            "Fetch discussion comments for each issue. "
            "Enabling this requires one request per issue and can be slow."
        ),
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=None,
        help="Seconds between refreshes; runs once when omitted.",
    )
    parser.add_argument(
        "--highlight-mine",
        action="store_true",
        help="Highlight findings submitted by you when supported by the terminal.",
    )
    return parser.parse_args()


def render_report(report: SherlockReport, args) -> None:
    timestamp = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
    print(f"{timestamp}")
    print(f"=== Sherlock {report.contest_id} — Findings ===")

    print(
        f"Total issues: {report.total_issues} "
        f"(valid: {report.total_valid_issues}, invalid: {report.total_invalid_issues})"
    )
    print(f"Total points: {report.total_points:.4f}")
    if report.prize_pool:
        print(f"Prize pool: ${report.prize_pool:,.2f}")

    print(
        f"My issues: {report.my_total_issues} "
        f"(valid: {report.my_valid_issues}, invalid: {report.my_total_issues - report.my_valid_issues})"
    )
    print(f"My expected reward: ${report.my_total_reward:,.2f}")

    if args.escalations:
        pending = max(report.total_escalated - report.total_resolved, 0)
        print(
            f"Escalations: {report.total_escalated} escalated | "
            f"{report.total_resolved} resolved | {pending} pending"
        )

    if args.comments:
        _render_comment_stats(report.issues.values())

    print()

    valid_findings = sorted(
        report.valid_findings,
        key=lambda finding: finding.main.reward,
        reverse=True,
    )

    if not valid_findings:
        print("No valid findings available to display.")
        return

    header = (
        f"{'#':<5} "
        f"{'Title':<73} "
        f"{'Sev':<6} "
        f"{'Dup':>3} "
        f"{'Points':>10} "
        f"{'Reward':>12} "
        f"{'Mine':>5}"
    )
    if args.escalations:
        header += f" {'Esc':>5} {'Res':>5}"

    divider = "-" * len(header)

    print(header)
    print(divider)

    highlight_mine = args.highlight_mine and _stdout_supports_color()

    for finding in valid_findings:
        row = _format_finding_row(finding, args.escalations)
        if highlight_mine and finding.mine:
            row = _highlight(row)
        print(row)

    print(divider)

    if args.escalations:
        _render_invalid_escalations(report)


def _render_comment_stats(issues: Iterable[SherlockIssue]) -> None:
    issues_list = list(issues)
    commented_invalid = sum(
        1 for issue in issues_list if issue.severity == 3 and issue.lead_judge_comments
    )
    print(f"LJ commented on {commented_invalid} invalid issues")

    last_comment = None
    last_issue: SherlockIssue | None = None
    for issue in issues_list:
        for comment in issue.lead_judge_comments:
            candidate_ts = comment.get("created_at") or 0
            if last_comment is None or candidate_ts > (last_comment.get("created_at") or 0):
                last_comment = comment
                last_issue = issue

    if last_comment and last_issue:
        created_at = last_comment.get("created_at")
        if created_at:
            timestamp = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M:%S")
            print(f"LJ last commented at {timestamp} on issue {last_issue.number}")


def _format_finding_row(finding: SherlockFinding, include_escalations: bool) -> str:
    title = truncate(finding.main.title, 73)
    row = (
        f"{str(finding.main.number):<5} "
        f"{title:<73} "
        f"{finding.main.severity_label:<6} "
        f"{len(finding.duplicates):>3} "
        f"{finding.main.points:>10.4f} "
        f"{finding.main.reward:>12.2f} "
        f"{yesno(finding.mine):>5}"
    )
    if include_escalations:
        row += (
            f" {yesno(finding.escalation_escalated):>5}"
            f" {yesno(finding.escalation_resolved):>5}"
        )
    return row


def _render_invalid_escalations(report: SherlockReport) -> None:
    issues = sorted(
        report.invalid_escalated_issues,
        key=lambda issue: issue.escalation_resolved,
        reverse=True,
    )
    if not issues:
        return

    print("\n=== Invalid issues (escalated) ===\n")
    header = (
        f"{'#':<5} "
        f"{'Title':<73} "
        f"{'Dup':>3} "
        f"{'Mine':>5} "
        f"{'Esc':>5} "
        f"{'Res':>5}"
    )
    divider = "-" * len(header)
    print(header)
    print(divider)
    for issue in issues:
        row = (
            f"{issue.number:<5} "
            f"{truncate(issue.title, 73):<73} "
            f"{len(issue.duplicate_ids):>3} "
            f"{yesno(issue.mine):>5} "
            f"{yesno(issue.escalation_escalated):>5} "
            f"{yesno(issue.escalation_resolved):>5}"
        )
        print(row)
    print(divider)


def _highlight(text: str) -> str:
    return f"\033[1;93m{text}\033[0m"


def _stdout_supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

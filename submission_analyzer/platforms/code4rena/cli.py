from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from datetime import datetime

from submission_analyzer.utils import truncate, yesno

from .models import Code4renaReport, Finding


def parse_code4rena_args():
    parser = argparse.ArgumentParser(
        prog="code4rena-analyzer",
        description="Analyze Code4rena contest submissions and estimate HM rewards.",
    )
    parser.add_argument(
        "contestId",
        help="Contest slug/identifier (visible in the Code4rena audit URL).",
    )
    parser.add_argument(
        "-p",
        "--prize-pool",
        type=float,
        default=None,
        help="High/medium prize pool allocation (USD). When omitted rewards are reported as $0.",
    )
    parser.add_argument(
        "-u",
        "--user",
        help="Your Code4rena handle. Defaults to the CODE4RENA_HANDLE environment variable.",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=None,
        help="Seconds between refreshes; runs once when omitted.",
    )
    parser.add_argument(
        "--include-invalid",
        action="store_true",
        help="Include invalid / non-winning findings in the table output.",
    )
    parser.add_argument(
        "--max-title",
        type=int,
        default=70,
        help="Trim finding titles to this length (default: 70).",
    )
    parser.add_argument(
        "--highlight-mine",
        action="store_true",
        help="Highlight findings that belong to you when supported by the terminal.",
    )
    return parser.parse_args()


def render_report(report: Code4renaReport, args) -> None:
    timestamp = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
    has_prize_pool = report.prize_pool > 0
    title_width = max(20, args.max_title)

    print(f"{timestamp}")
    print(f"=== Code4rena {report.contest_id} — Findings ===")
    print(
        f"Submissions: {report.total_submissions} (primary: {report.total_primary}) | "
        f"Judged: {report.total_judged}"
    )
    print(
        f"Valid findings: {report.total_valid_findings}/{report.total_primary} | "
        f"Total points: {report.total_points:.2f}"
    )
    if has_prize_pool:
        print(f"Prize pool: ${report.prize_pool:,.2f}")
    if report.my_total_submissions:
        print(
            f"My submissions: {report.my_total_submissions} total "
            f"My valid findings: {report.my_valid_findings}"
        )
    if has_prize_pool and report.my_reward:
        print(f"My expected reward: ${report.my_reward:,.2f}")

    print()

    findings_to_show = _filter_findings(report.findings.values(), args.include_invalid)
    if not findings_to_show:
        print("No findings available to display.")
        return

    header = (
        f"{'#':<4} "
        f"{'Title':<{title_width}} "
        f"{'Sev':<6} "
        f"{'Subs':>4} "
        f"{'Pts':>9}"
    )
    if has_prize_pool:
        header += f" {'Reward':>12}"
    header += f" {'Mine':>5}"

    divider = "-" * len(header)
    print(header)
    print(divider)

    sorted_findings = sorted(
        findings_to_show,
        key=lambda f: (
            -(f.reward if has_prize_pool else f.points),
            -f.points,
            f.title.lower(),
        ),
    )

    highlight_mine = args.highlight_mine and _stdout_supports_color()

    for idx, finding in enumerate(sorted_findings, start=1):
        title = truncate(finding.title, title_width)
        severity = (finding.severity or "-").capitalize()
        reward = f"${finding.reward:,.2f}" if has_prize_pool else "-"
        row = (
            f"{str(idx):<4} "
            f"{title:<{title_width}} "
            f"{severity:<6} "
            f"{finding.subs:>4} "
            f"{finding.points:>9.4f}"
        )
        if has_prize_pool:
            row += f" {reward:>12}"
        row += f"{yesno(finding.mine):>5}"
        if highlight_mine and finding.mine:
            row = _highlight(row)
        print(row)


def _filter_findings(findings: Iterable[Finding], include_invalid: bool) -> list[Finding]:
    visible: list[Finding] = []
    for finding in findings:
        if finding.is_valid and finding.severity in {"high", "medium"}:
            visible.append(finding)
            continue
        if include_invalid:
            visible.append(finding)
    return visible


def _highlight(text: str) -> str:
    return f"\033[1;93m{text}\033[0m"


def _stdout_supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

from __future__ import annotations

from collections.abc import Iterable

from .models import SherlockIssue


def get_valids(issues: Iterable[SherlockIssue]) -> list[SherlockIssue]:
    return [issue for issue in issues if issue.is_valid]


def get_invalids_escalated(issues: Iterable[SherlockIssue]) -> list[SherlockIssue]:
    return [
        issue
        for issue in issues
        if issue.severity == 3 and issue.escalation_escalated
    ]


def calculate_issue_points(submissions_count: int, severity: int | None) -> float:
    if severity is None:
        return 0.0
    base_points = 5 if severity == 1 else 1 if severity == 2 else 0
    if submissions_count <= 0:
        return 0.0
    return base_points * (0.9 ** (submissions_count - 1)) / submissions_count

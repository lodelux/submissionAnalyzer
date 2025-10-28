from __future__ import annotations

from collections.abc import Iterable

from .models import Issue


def get_valids(issues: Iterable[Issue]) -> list[Issue]:
    return [issue for issue in issues if issue.severity in (1, 2)]


def get_invalids_escalated(issues: Iterable[Issue]) -> list[Issue]:
    return [
        issue
        for issue in issues
        if issue.severity == 3 and issue.escalation.get("escalated")
    ]


def is_issues_mutated(old: dict[str, Issue], new: dict[str, Issue]) -> bool:
    if set(old.keys()) != set(new.keys()):
        return True

    for key in new.keys():
        if old[key] != new[key]:
            print(old[key].snapshot())
            print(new[key].snapshot())
            return True
    return False


def calculate_issue_points(submissions_count: int, severity: int | None) -> float:
    if severity is None:
        return 0.0
    base_points = 5 if severity == 1 else 1 if severity == 2 else 0
    if submissions_count <= 0:
        return 0.0
    return base_points * (0.9 ** (submissions_count - 1)) / submissions_count

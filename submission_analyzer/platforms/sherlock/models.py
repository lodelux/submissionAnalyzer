from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SEVERITY_LABELS = {1: "High", 2: "Medium"}


@dataclass
class SherlockIssue:
    id: str
    number: int
    title: str
    severity: int | None = None
    is_main: bool = False
    is_submitted_by_user: bool = False
    duplicate_of: str | None = None
    duplicate_ids: list[str] = field(default_factory=list)
    comments: list[dict[str, Any]] = field(default_factory=list)
    points: float = 0.0
    reward: float = 0.0
    escalation_escalated: bool = False
    escalation_resolved: bool = False

    @property
    def severity_label(self) -> str:
        if self.severity is None:
            return "-"
        return SEVERITY_LABELS.get(self.severity, str(self.severity))

    @property
    def lead_judge_comments(self) -> list[dict[str, Any]]:
        return [c for c in self.comments if c.get("is_lead_judge")]

    @property
    def is_valid(self) -> bool:
        return self.severity in (1, 2)

    @property
    def mine(self) -> bool:
        return bool(self.is_submitted_by_user)

    def snapshot(self) -> tuple[Any, ...]:
        return (
            self.id,
            self.number,
            self.title,
            self.severity,
            self.is_main,
            self.duplicate_of,
            tuple(sorted(self.duplicate_ids)),
            self.is_submitted_by_user,
            round(self.points, 8),
            round(self.reward, 8),
            self.escalation_escalated,
            self.escalation_resolved,
            tuple(sorted(c.get("id") for c in self.lead_judge_comments)),
        )

    def __eq__(self, other):
        if not isinstance(other, SherlockIssue):
            return NotImplemented
        return self.snapshot() == other.snapshot()


@dataclass
class SherlockFinding:
    main: SherlockIssue
    duplicates: list[SherlockIssue] = field(default_factory=list)

    @property
    def submissions_count(self) -> int:
        return 1 + len(self.duplicates)

    @property
    def mine(self) -> bool:
        if self.main.mine:
            return True
        return any(dup.mine for dup in self.duplicates)

    @property
    def is_valid(self) -> bool:
        return self.main.is_valid

    @property
    def escalation_escalated(self) -> bool:
        if self.main.escalation_escalated:
            return True
        return any(dup.escalation_escalated for dup in self.duplicates)

    @property
    def escalation_resolved(self) -> bool:
        escalated_members = [
            issue
            for issue in [self.main, *self.duplicates]
            if issue.escalation_escalated
        ]
        if not escalated_members:
            return False
        return all(issue.escalation_resolved for issue in escalated_members)


@dataclass
class SherlockReport:
    contest_id: int
    issues: dict[str, SherlockIssue]
    findings: list[SherlockFinding]
    prize_pool: float
    total_points: float
    my_total_reward: float
    my_total_issues: int
    my_valid_issues: int
    total_escalated: int
    total_resolved: int

    @property
    def total_issues(self) -> int:
        return len(self.issues)

    @property
    def total_valid_issues(self) -> int:
        return sum(1 for issue in self.issues.values() if issue.is_valid)

    @property
    def total_invalid_issues(self) -> int:
        return self.total_issues - self.total_valid_issues

    @property
    def valid_findings(self) -> list[SherlockFinding]:
        return [finding for finding in self.findings if finding.is_valid]

    @property
    def invalid_escalated_issues(self) -> list[SherlockIssue]:
        return [
            issue
            for issue in self.issues.values()
            if issue.severity == 3 and issue.escalation_escalated
        ]

    def snapshot(self) -> tuple[Any, ...]:
        issues_snapshot = tuple(
            sorted((issue.id, issue.snapshot()) for issue in self.issues.values())
        )
        return (
            self.contest_id,
            round(self.prize_pool, 2),
            round(self.total_points, 6),
            round(self.my_total_reward, 6),
            self.my_total_issues,
            self.my_valid_issues,
            self.total_escalated,
            self.total_resolved,
            issues_snapshot,
        )

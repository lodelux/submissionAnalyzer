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

    @classmethod
    def from_api(cls, issue_id: str, payload: dict[str, Any]) -> "SherlockIssue":
        return cls(
            id=str(issue_id),
            number=int(payload.get("number") or 0),
            title=str(payload.get("title") or ""),
        )

    def apply_family_member(
        self,
        member_payload: dict[str, Any],
        *,
        severity: int | None,
        is_main: bool,
        main_issue_id: str | None = None,
    ) -> None:
        if severity is not None:
            self.severity = severity
        self.is_main = is_main
        self.is_submitted_by_user = bool(
            member_payload.get("was_submitted_by_user")
        )
        self.escalation_escalated = bool(
            member_payload.get("has_escalation_comment")
        )
        self.escalation_resolved = bool(
            member_payload.get("escalation_resolved")
        )
        if is_main:
            self.duplicate_of = None
        elif main_issue_id is not None:
            self.duplicate_of = main_issue_id

    def add_duplicate(self, duplicate_id: str) -> None:
        if duplicate_id not in self.duplicate_ids:
            self.duplicate_ids.append(duplicate_id)

    def attach_comments(self, comments: list[dict[str, Any]]) -> None:
        self.comments = sorted(
            comments or [],
            key=lambda c: c.get("created_at") or 0,
        )

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

    @classmethod
    def from_api(
        cls,
        payload: dict[str, Any],
        issues: dict[str, SherlockIssue],
    ) -> "SherlockFinding | None":
        if not isinstance(payload, dict):
            return None

        main_details = payload.get("main") or {}
        main_id = main_details.get("issue")
        if main_id is None:
            return None

        main_issue = issues.get(str(main_id))
        if not main_issue:
            return None

        severity = payload.get("primary_severity")
        main_issue.apply_family_member(
            main_details,
            severity=severity,
            is_main=True,
        )

        duplicates: list[SherlockIssue] = []
        for dup_details in payload.get("duplicates") or []:
            dup_id = dup_details.get("issue")
            if dup_id is None:
                continue
            dup_issue = issues.get(str(dup_id))
            if not dup_issue:
                continue
            dup_issue.apply_family_member(
                dup_details,
                severity=severity,
                is_main=False,
                main_issue_id=main_issue.id,
            )
            main_issue.add_duplicate(dup_issue.id)
            duplicates.append(dup_issue)

        return cls(main=main_issue, duplicates=duplicates)

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

    def iter_issues(self) -> tuple[SherlockIssue, ...]:
        return (self.main, *self.duplicates)

    def assign_points(self) -> float:
        issues = self.iter_issues()
        for issue in issues:
            issue.points = 0.0

        if not self.main.is_main or not self.main.is_valid:
            return 0.0

        from .utils import calculate_issue_points

        submissions_count = self.submissions_count
        points = calculate_issue_points(submissions_count, self.main.severity)
        for issue in issues:
            issue.points = points
        return points * submissions_count

    def assign_rewards(self, total_points: float, prize_pool: float) -> None:
        issues = self.iter_issues()
        if total_points <= 0 or prize_pool <= 0:
            for issue in issues:
                issue.reward = 0.0
            return
        for issue in issues:
            if issue.points <= 0:
                issue.reward = 0.0
            else:
                issue.reward = (issue.points / total_points) * prize_pool


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

    @classmethod
    def from_data(
        cls,
        *,
        contest_id: int,
        issues: dict[str, SherlockIssue],
        findings: list[SherlockFinding],
        prize_pool: float,
        total_points: float,
    ) -> "SherlockReport":
        my_total_reward = 0.0
        my_total_issues = 0
        my_valid_issues = 0
        total_escalated = 0
        total_resolved = 0

        for issue in issues.values():
            if issue.mine:
                my_total_issues += 1
                if issue.is_valid:
                    my_valid_issues += 1
                    my_total_reward += issue.reward
            if issue.escalation_escalated:
                total_escalated += 1
            if issue.escalation_resolved:
                total_resolved += 1

        return cls(
            contest_id=contest_id,
            issues=issues,
            findings=findings,
            prize_pool=prize_pool,
            total_points=total_points,
            my_total_reward=my_total_reward,
            my_total_issues=my_total_issues,
            my_valid_issues=my_valid_issues,
            total_escalated=total_escalated,
            total_resolved=total_resolved,
        )

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

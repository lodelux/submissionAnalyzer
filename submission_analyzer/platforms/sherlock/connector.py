from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .api import SherlockAPI
from .models import SherlockFinding, SherlockIssue, SherlockReport
from .utils import calculate_issue_points

ProgressCallback = Callable[[int, int, SherlockIssue | None], None]


class SherlockConnector:
    def __init__(self, contest_id: int, session_id: str | None):
        self.api = SherlockAPI(contest_id, session_id)
        self.contest_id = contest_id

    def build_report(
        self,
        include_comments: bool = False,
        progress_callback: ProgressCallback | None = None,
    ) -> SherlockReport:
        issues = self._fetch_issues()
        families = self._extract_families(self.api.getJudge())
        self._apply_judging_details(issues, families)

        if include_comments:
            self._attach_comments(issues, progress_callback)

        total_points = self._assign_points(issues)
        contest = self.api.getContest() or {}
        prize_pool = float(contest.get("prize_pool") or 0.0)
        self._assign_rewards(issues, total_points, prize_pool)

        findings = self._build_findings(issues)

        my_total_reward = 0
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

        return SherlockReport(
            contest_id=self.contest_id,
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

    def _fetch_issues(self) -> dict[str, SherlockIssue]:
        titles_payload = self.api.getTitles() or {}
        issues: dict[str, SherlockIssue] = {}
        for issue_id, data in titles_payload.items():
            issue_key = str(issue_id)
            number = data.get("number")
            title = data.get("title") or ""
            issues[issue_key] = SherlockIssue(
                id=issue_key,
                number=number,
                title=title,
            )
        return issues

    def _extract_families(self, judge_payload: Any) -> list[dict[str, Any]]:
        if isinstance(judge_payload, dict):
            families = judge_payload.get("families") or []
            if isinstance(families, list):
                return families
            return []
        if isinstance(judge_payload, list):
            for item in judge_payload:
                if isinstance(item, dict):
                    families = item.get("families")
                    if isinstance(families, list):
                        return families
        return []

    def _apply_judging_details(
        self,
        issues: dict[str, SherlockIssue],
        families: list[dict[str, Any]],
    ) -> None:
        for family in families:
            main_details = family.get("main") or {}
            main_id = str(main_details.get("issue"))
            main_issue = issues.get(main_id)
            if not main_issue:
                continue

            severity = family.get("primary_severity")

            main_issue.is_main = True
            if severity is not None:
                main_issue.severity = severity
            main_issue.is_submitted_by_user = bool(
                main_details.get("was_submitted_by_user")
            )
            main_issue.escalation_escalated = bool(
                main_details.get("has_escalation_comment")
            )
            main_issue.escalation_resolved = bool(
                main_details.get("escalation_resolved")
            )

            duplicates = family.get("duplicates") or []
            for dup_details in duplicates:
                dup_id = str(dup_details.get("issue"))
                dup_issue = issues.get(dup_id)
                if not dup_issue:
                    continue
                dup_issue.duplicate_of = main_issue.id
                dup_issue.severity = severity
                dup_issue.is_submitted_by_user = bool(
                    dup_details.get("was_submitted_by_user")
                )
                dup_issue.escalation_escalated = bool(
                    dup_details.get("has_escalation_comment")
                )
                dup_issue.escalation_resolved = bool(
                    dup_details.get("escalation_resolved")
                )
                if dup_id not in main_issue.duplicate_ids:
                    main_issue.duplicate_ids.append(dup_id)

    def _attach_comments(
        self,
        issues: dict[str, SherlockIssue],
        progress_callback: ProgressCallback | None,
    ) -> None:
        total = len(issues)
        for idx, issue in enumerate(issues.values(), start=1):
            if progress_callback:
                progress_callback(idx, total, issue)
            discussion = self.api.getDiscussions(issue.id) or {}
            comments = discussion.get("comments") or []
            issue.comments = sorted(
                comments,
                key=lambda c: c.get("created_at") or 0,
            )
        if progress_callback:
            progress_callback(total, total, None)

    def _assign_points(self, issues: dict[str, SherlockIssue]) -> float:
        total_points = 0.0
        for issue in issues.values():
            if not issue.is_main or not issue.is_valid:
                continue
            duplicates = [
                dup_id for dup_id in issue.duplicate_ids if dup_id in issues
            ]
            subs_count = 1 + len(duplicates)
            points = calculate_issue_points(subs_count, issue.severity)
            issue.points = points
            total_points += points * subs_count
            for dup_id in duplicates:
                dup_issue = issues.get(dup_id)
                if dup_issue:
                    dup_issue.points = points
        return total_points

    def _assign_rewards(
        self,
        issues: dict[str, SherlockIssue],
        total_points: float,
        prize_pool: float,
    ) -> None:
        if total_points <= 0 or prize_pool <= 0:
            for issue in issues.values():
                issue.reward = 0.0
            return
        for issue in issues.values():
            if issue.points <= 0:
                issue.reward = 0.0
            else:
                issue.reward = (issue.points / total_points) * prize_pool

    def _build_findings(
        self, issues: dict[str, SherlockIssue]
    ) -> list[SherlockFinding]:
        findings: list[SherlockFinding] = []
        for issue in issues.values():
            if not issue.is_main:
                continue
            duplicates = [
                issues[dup_id] for dup_id in issue.duplicate_ids if dup_id in issues
            ]
            findings.append(SherlockFinding(main=issue, duplicates=duplicates))
        return findings

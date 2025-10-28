from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .api import SherlockAPI
from .models import SherlockFinding, SherlockIssue, SherlockReport

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
        findings = self._build_findings(issues, families)

        if include_comments:
            self._attach_comments(issues, progress_callback)

        total_points = self._assign_points(findings)
        contest = self.api.getContest() or {}
        prize_pool = float(contest.get("prize_pool") or 0.0)
        self._assign_rewards(findings, total_points, prize_pool)

        return SherlockReport.from_data(
            contest_id=self.contest_id,
            issues=issues,
            findings=findings,
            prize_pool=prize_pool,
            total_points=total_points,
        )

    def _fetch_issues(self) -> dict[str, SherlockIssue]:
        titles_payload = self.api.getTitles() or {}
        issues: dict[str, SherlockIssue] = {}
        for issue_id, data in titles_payload.items():
            issue_key = str(issue_id)
            issues[issue_key] = SherlockIssue.from_api(issue_key, data or {})
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

    def _build_findings(
        self,
        issues: dict[str, SherlockIssue],
        families: list[dict[str, Any]],
    ) -> list[SherlockFinding]:
        findings: list[SherlockFinding] = []
        for family in families:
            finding = SherlockFinding.from_api(family, issues)
            if finding:
                findings.append(finding)
        return findings

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
            issue.attach_comments(comments)
        if progress_callback:
            progress_callback(total, total, None)

    def _assign_points(self, findings: list[SherlockFinding]) -> float:
        total_points = 0.0
        for finding in findings:
            total_points += finding.assign_points()
        return total_points

    def _assign_rewards(
        self,
        findings: list[SherlockFinding],
        total_points: float,
        prize_pool: float,
    ) -> None:
        for finding in findings:
            finding.assign_rewards(total_points, prize_pool)

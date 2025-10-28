from __future__ import annotations

from .api import Code4renaAPI
from .models import Code4renaIssue, Code4renaReport, Finding


class Code4renaConnector:
    def __init__(
        self,
        contest_id: str,
        session_id: str | None,
        prize_pool: float | None = None,
        user: str | None = "",
    ):
        self.api = Code4renaAPI(contest_id, session_id)
        self.contest_id = contest_id
        self.prize_pool = float(prize_pool) if prize_pool not in (None, "") else 0.0
        self.user = (user or "").strip()

    def getAllSubmissions(self) -> list[Code4renaIssue]:
        return self.api.getAllSubmissions()

    def getAllPrimary(self, subs: list[Code4renaIssue]) -> list[Code4renaIssue]:
        return [s for s in subs if s.is_primary]

    def getMySubs(self, subs: list[Code4renaIssue]) -> list[Code4renaIssue]:
        if not self.user:
            return []
        return [s for s in subs if s.submitter_handle == self.user]

    def getTotalJudged(self, subs: list[Code4renaIssue]) -> int:
        return sum(1 for s in subs if s.evaluations)

    def getFindingTotalPoints(self, severity: str, subs: int) -> float:
        if severity == "high":
            return 10 * (0.85 ** (subs - 1))
        if severity == "medium":
            return 3 * (0.85 ** (subs - 1))
        return 0.0

    def build_report(self) -> Code4renaReport:
        submissions = self.getAllSubmissions()
        primaries = self.getAllPrimary(submissions)
        findings: dict[str, Finding] = {}
        total_points = 0.0

        for sub in primaries:
            latest = sub.latest_evaluations
            severity = (
                (latest.severity if latest and latest.severity else sub.submitted_severity or "")
                .lower()
                .strip()
            )
            validity = (
                (latest.validity if latest and latest.validity else "")
                .lower()
                .strip()
                or "unknown"
            )
            duplicates = sub.finding_duplicates or 1
            finding_id = sub.finding_uid or sub.uid
            points = self._points_for_finding(severity, validity, duplicates)

            findings[finding_id] = Finding(
                id=finding_id,
                title=sub.title or "",
                subs=duplicates,
                severity=severity or "-",
                validity=validity,
                points=points,
            )
            total_points += points

        my_total_submissions = 0
        my_primary_submissions = 0
        if self.user:
            for sub in submissions:
                if sub.submitter_handle == self.user:
                    my_total_submissions += 1
                    finding = findings.get(sub.finding_uid or sub.uid)
                    if finding:
                        finding.mine = True
            for sub in primaries:
                if sub.submitter_handle == self.user:
                    my_primary_submissions += 1

        prize_pool = self.prize_pool
        for finding in findings.values():
            finding.reward = finding.getSingleReward(prize_pool, total_points)

        my_reward = sum(f.reward for f in findings.values() if f.mine)
        total_valid_findings = sum(1 for f in findings.values() if f.is_valid)
        my_valid_findings = sum(1 for f in findings.values() if f.mine and f.is_valid)

        return Code4renaReport(
            contest_id=self.contest_id,
            findings=findings,
            total_points=total_points,
            total_submissions=len(submissions),
            total_primary=len(primaries),
            total_judged=self.getTotalJudged(submissions),
            prize_pool=prize_pool,
            my_total_submissions=my_total_submissions,
            my_primary_submissions=my_primary_submissions,
            total_valid_findings=total_valid_findings,
            my_valid_findings=my_valid_findings,
            my_reward=my_reward,
        )

    def _points_for_finding(
        self,
        severity: str,
        validity: str,
        duplicates: int,
    ) -> float:
        if validity != "valid":
            return 0.0
        if severity not in {"high", "medium"}:
            return 0.0
        duplicates = max(int(duplicates or 1), 1)
        return float(self.getFindingTotalPoints(severity, duplicates))

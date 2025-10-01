from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


@dataclass
class Code4renaEvaluation:
    uid: str | None
    type: str | None
    value: str | None
    user_uid: str | None
    user_role: str | None
    created_at: datetime | None
    submission_uid: str | None
    finding_uid: str | None

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Code4renaEvaluation":
        return cls(
            uid=payload.get("uid"),
            type=payload.get("type"),
            value=payload.get("value"),
            user_uid=payload.get("userUid"),
            user_role=payload.get("userAuditRole"),
            created_at=_parse_datetime(payload.get("createdAt")),
            submission_uid=payload.get("submissionUid"),
            finding_uid=payload.get("findingUid"),
        )


@dataclass
class Code4renaLatestEvaluations:
    credit: str | None = None
    mitigation_status: str | None = None
    quality: str | None = None
    rank: str | None = None
    severity: str | None = None
    validity: str | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Code4renaLatestEvaluations":
        if not payload:
            return cls()
        return cls(
            credit=payload.get("credit"),
            mitigation_status=payload.get("mitigationStatus"),
            quality=payload.get("quality"),
            rank=payload.get("rank"),
            severity=payload.get("severity"),
            validity=payload.get("validity"),
            updated_at=_parse_datetime(payload.get("updatedAt")),
        )


@dataclass
class Code4renaIssue:
    uid: str
    number: int
    title: str
    severity: str
    audit_uid: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    mitigation_of: str | None = None
    mitigation_status: str | None = None
    team: str | None = None
    sensitivity: str | None = None
    submitter_uid: str | None = None
    submitter_handle: str | None = None
    evaluations: list[Code4renaEvaluation] = field(default_factory=list)
    latest_evaluations: Code4renaLatestEvaluations | None = None
    finding_uid: str | None = None
    finding_number: int | None = None
    finding_duplicates: int | None = None
    filtered_duplicates: int | None = None
    is_primary: bool | None = None

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Code4renaIssue":
        user = payload.get("user") or {}
        finding = payload.get("finding") or {}
        evaluations = [
            Code4renaEvaluation.from_api(e)
            for e in payload.get("evaluations", [])
        ]
        latest_evaluations = Code4renaLatestEvaluations.from_api(
            payload.get("latestEvaluations")
        )

        return cls(
            uid=payload.get("uid"),
            number=payload.get("number"),
            title=payload.get("title"),
            severity=payload.get("severity"),
            audit_uid=payload.get("auditUid"),
            created_at=_parse_datetime(payload.get("createdAt")),
            updated_at=_parse_datetime(payload.get("updatedAt")),
            deleted_at=_parse_datetime(payload.get("deletedAt")),
            mitigation_of=payload.get("mitigationOf"),
            mitigation_status=payload.get("mitigationStatus"),
            team=payload.get("team"),
            sensitivity=payload.get("sensitivity"),
            submitter_uid=user.get("uid"),
            submitter_handle=user.get("handle"),
            evaluations=evaluations,
            latest_evaluations=latest_evaluations,
            finding_uid=finding.get("uid"),
            finding_number=finding.get("number"),
            finding_duplicates=finding.get("duplicates"),
            filtered_duplicates=payload.get("filteredDuplicates"),
            is_primary=payload.get("isPrimary"),
        )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    



@dataclass
class Finding:
    id: str
    title: str
    subs: int
    severity: str
    validity: str
    points: int = 0
    mine: bool = False


    def getSinglePoints(self):
        return self.points / self.subs 
    
    def getSingleReward(self, prizePool, totalPointsAllFindings):
        if totalPointsAllFindings == 0:
            return 0
        pts = self.getSinglePoints()
        return (pts / totalPointsAllFindings) * prizePool
    
    def getTotalReward(self, prizePool, totalPointsAllFindings):
        if totalPointsAllFindings == 0:
            return 0
        return (self.points / totalPointsAllFindings) * prizePool
    


    



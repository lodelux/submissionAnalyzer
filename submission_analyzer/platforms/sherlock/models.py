from __future__ import annotations


class Issue:
    def __init__(self, id: str | None = None, number: int | None = None, title: str | None = None):
        self.id = id
        self.number = number
        self.title = title
        self.isSubmittedByUser = False
        self.isMain = False
        self.duplicateOf: Issue | None = None
        self.duplicates: list[Issue] = []
        self.comments = []  # ordered from youngest to oldest
        self.severity = None
        self.points: float = 0
        self.reward: float = 0
        self.escalation = {"escalated": False, "resolved": False}

    @property
    def leadJudgeComments(self):
        # still ordered from youngest to oldest
        return [c for c in self.comments if c.get("is_lead_judge")]

    def snapshot(self):
        return (
            self.id,
            self.number,
            self.title,
            self.isSubmittedByUser,
            self.isMain,
            self.severity,
            tuple(sorted(d.id for d in self.duplicates)),
            self.duplicateOf.id if self.duplicateOf else None,
            round(self.points, 8),
            round(self.reward, 8),
            (
                self.escalation.get("escalated", False),
                self.escalation.get("resolved", False),
            ),
            tuple(sorted((c.get("id") for c in self.leadJudgeComments))),
        )

    def __eq__(self, other):
        if not isinstance(other, Issue):
            return NotImplemented
        return self.snapshot() == other.snapshot()

import os
from dotenv import load_dotenv
from submission_analyzer.api.code4rena_api import Code4renaAPI
from submission_analyzer.models.code4rena_issue import Code4renaIssue, Finding
from submission_analyzer.utils import truncate

class Code4renaConnector:
    def __init__(self, contest_id, sessionId, hmPool, user = ""):
        sessionId = sessionId
        self.api = Code4renaAPI(contest_id, sessionId)
        self.hmPool = hmPool
        self.user = user

    def getAllSubmissions(self):
        return self.api.getAllSubmissions()
            
    
    def getAllPrimary(self, subs: list[Code4renaIssue]) -> list[Code4renaIssue]:
        return [s for s in subs if s.is_primary]
    

    def getMySubs(self, subs: list[Code4renaIssue]) -> list[Code4renaIssue]:
        return [s for s in subs if s.submitter_handle == self.user]
    
    def getTotalJudged(self,subs: list[Code4renaIssue]) -> int:
        return sum([1 for s in subs if len(s.evaluations) ])

    
    def getFindingPoints(self, severity: str, subs: int) -> int:
        if severity == "high":
            return 10 * (0.85 ** (subs - 1))
        elif severity == "medium":
            return 3 * (0.85 ** (subs - 1))
        else:
            return 0

    



def _print_findings_summary(findings: dict[str, Finding], prize_pool: float, total_points: float) -> None:
    if not findings:
        print("No findings available to display.")
        return

    sorted_findings = sorted(findings.values(), key=lambda f: f.getSingleReward(hmPool,totalPoints), reverse=True)
    headers = (
        "#",
        "Finding",
        "Severity",
        "Subs",
        "Points",
        "Reward",
        "Mine",
    )

    table_rows: list[tuple[str, ...]] = []
    for index, finding in enumerate(sorted_findings, start=1):
        if finding.validity != "valid" or not (finding.severity == "high" or finding.severity == "medium"):
            continue
        reward = finding.getSingleReward(prize_pool, total_points)
        table_rows.append(
            (
                str(index),
                truncate(finding.title or "-"),
                finding.severity or "-",
                str(finding.subs),
                f"{finding.points:.2f}",
                f"${reward:,.2f}",
                "x" if finding.mine else ""
            )
        )

    column_widths = [len(header) for header in headers]
    for row in table_rows:
        for column_index, cell in enumerate(row):
            column_widths[column_index] = max(column_widths[column_index], len(cell))

    header_line = "  ".join(header.ljust(column_widths[idx]) for idx, header in enumerate(headers))
    divider_line = "  ".join("-" * width for width in column_widths)

    print(header_line)
    print(divider_line)
    for row in table_rows:
        print("  ".join(cell.ljust(column_widths[idx]) for idx, cell in enumerate(row)))

    my_total = sum(finding.getSingleReward(prize_pool, total_points) for finding in sorted_findings if finding.mine)
    print()
    print(f"Total findings: {len(sorted_findings)}")
    print(f"Total points: {total_points:.2f}")
    print(f"Prize pool: ${prize_pool:,.2f}")
    if my_total:
        print(f"My potential reward: ${my_total:,.2f}")


if __name__ == "__main__":
    load_dotenv()

    contestId = "gtn2Umg6KsC"
    hmPool = 96000
    user = "lodelux"
    sessionId = os.getenv("SESSION_CODE4")
    connector = Code4renaConnector(contestId, sessionId, hmPool, user)

    submissions = connector.getAllSubmissions()
    primaries = connector.getAllPrimary(submissions)

    findings: dict[str, Finding] = {}
    totalPoints = 0
    for sub in primaries:
        validity = sub.latest_evaluations.validity if sub.latest_evaluations else "invalid"
        pts = connector.getFindingPoints(sub.latest_evaluations.severity if sub.latest_evaluations else sub.severity, sub.finding_duplicates or 1) if validity == "valid" else 0
        totalPoints += pts
        findings[sub.finding_uid] = Finding(
            id=sub.finding_uid,
            title = sub.title,
            subs=sub.finding_duplicates or 1,
            severity=sub.latest_evaluations.severity if sub.latest_evaluations else sub.severity,
            validity=sub.latest_evaluations.validity if sub.latest_evaluations else "invalid",
            points=pts,
        )
    
    for mys in connector.getMySubs(submissions):
        finding = findings.get(mys.finding_uid)
        if finding:
            finding.mine = True


    _print_findings_summary(findings, hmPool, totalPoints)

    print(f'Total judged submissions: {connector.getTotalJudged(submissions)} out of {len(submissions)}')
       


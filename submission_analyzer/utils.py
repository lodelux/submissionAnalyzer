import time

import requests

from submission_analyzer.models.sherlock_issue import Issue


def getValids(issues: list[Issue]):
    return [issue for issue in issues if issue.severity == 1 or issue.severity == 2]


def getInvalidsEscalated(issues: list[Issue]):
    return [
        issue
        for issue in issues
        if issue.severity == 3 and issue.escalation["escalated"]
    ]


def isIssuesMutated(oldIssues:dict[str,Issue], newIssues:dict[str,Issue]):
    if set(oldIssues.keys()) != set(newIssues.keys()):
        return True
    
    for k in newIssues.keys():
        if oldIssues[k] != newIssues[k]:
            print(oldIssues[k].snapshot())
            print(newIssues[k].snapshot())
            return True
    return False


def calculate_issue_points(submissions_count, severity):
    # severity: 1 = high, 2 = medium 3 = invalid
    base_points = 5 if severity == 1 else 1 if severity == 2 else 0
    return base_points * (0.9 ** (submissions_count - 1)) / submissions_count


def truncate(text: str, max_len: int = 70) -> str:
    if text is None:
        return ""
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def yesno(flag: bool) -> str:
    return "Y" if flag else "N"


def get_json_with_retry(
    url: str,
    headers: dict[str, str] | None = None,
    max_attempts: int = 15,
    first_timeout: float = 1.0,
):
    attempts = 0
    headers = headers or {}
    resp = None
    while attempts < max_attempts:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        sleep_time = first_timeout * (2 ** attempts)

        print(
            f"NETWORK ERROR: attempt {attempts}, retrying in {sleep_time}s - {resp.status_code} {resp.text}"
        )
        time.sleep(sleep_time)
        attempts += 1
    resp.raise_for_status()

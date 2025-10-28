import time

import requests


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

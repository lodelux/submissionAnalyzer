#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import traceback
from typing import Any

from dotenv import load_dotenv

from submission_analyzer.monitoring import setup_sentry
from submission_analyzer.notifiers.telegram_notifier import TelegramBot

from .cli import parse_sherlock_args, render_report
from .connector import ProgressCallback, SherlockConnector
from .models import SherlockIssue, SherlockReport

MAX_RETRIES = 5
FALLBACK_RETRY_DELAY = 600


async def main():
    args = parse_sherlock_args()

    load_dotenv()
    setup_sentry()

    session_id = os.getenv("SESSION_SHERLOCK")
    telegram_bot = TelegramBot(os.getenv("BOT_TOKEN"), os.getenv("CHAT_ID"))
    connector = SherlockConnector(args.contestId, session_id)

    last_snapshot: tuple[Any, ...] | None = None
    retries = 0
    timeout = args.timeout
    retry_delay = timeout if timeout and timeout > 0 else FALLBACK_RETRY_DELAY

    progress_callback: ProgressCallback | None = (
        _comment_progress if args.comments else None
    )

    while retries < MAX_RETRIES:
        try:
            report = connector.build_report(
                include_comments=args.comments,
                progress_callback=progress_callback,
            )
            snapshot = report.snapshot()
            if snapshot != last_snapshot:
                render_report(report, args)
                summary = _build_notification_summary(report)
                if summary:
                    await telegram_bot.sendMessage(summary)
                last_snapshot = snapshot
            retries = 0
            if timeout is None:
                return
            await asyncio.sleep(timeout)
        except Exception as exc:
            retries += 1
            print(f"[sherlock] error while refreshing data: {exc}")
            traceback.print_exc()
            if retries >= MAX_RETRIES:
                raise RuntimeError("Exceeded maximum retries") from exc
            await asyncio.sleep(retry_delay)

    raise RuntimeError("Exceeded maximum retries")


def _build_notification_summary(report: SherlockReport) -> str:
    return (
        f"Reward: {report.my_total_reward:.2f} | "
        f"Valid issues: {report.my_valid_issues}/{report.my_total_issues} | "
        f"Escalations resolved: {report.total_resolved}/{report.total_escalated}"
    )


def _comment_progress(
    index: int, total: int, issue: SherlockIssue | None
) -> None:
    if issue is None:
        print()
        return
    print(
        f"Fetching comments for issue {issue.number} - {index}/{total}",
        end="\r",
        flush=True,
    )


def main_sync():
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()

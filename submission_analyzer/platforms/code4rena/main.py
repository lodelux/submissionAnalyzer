#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import traceback

from dotenv import load_dotenv

from submission_analyzer.monitoring import setup_sentry
from submission_analyzer.notifiers.telegram_notifier import TelegramBot

from .cli import parse_code4rena_args, render_report
from .connector import Code4renaConnector

MAX_RETRIES = 5
FALLBACK_RETRY_DELAY = 600


async def main():
    args = parse_code4rena_args()

    load_dotenv()
    setup_sentry()

    username = os.getenv("CODE4_USER").strip()
    password = os.getenv("CODE4_PASS").strip()

    contest_id = args.contestId
    handle = (args.user if args.user else username).strip()
    prize_pool = args.prize_pool

    connector = Code4renaConnector(
        contest_id,
        username,
        password,
        prize_pool=prize_pool,
        handle=handle,
    )

    telegram_bot = TelegramBot(os.getenv("BOT_TOKEN"), os.getenv("CHAT_ID"))

    last_snapshot = None
    retries = 0
    timeout = args.timeout
    retry_delay = (
        args.timeout if args.timeout and args.timeout > 0 else FALLBACK_RETRY_DELAY
    )

    while retries < MAX_RETRIES:
        try:
            report = connector.build_report()
            snapshot = report.snapshot()
            if snapshot != last_snapshot:
                render_report(report, args)
                summary = _build_notification_summary(report, connector.handle)
                if summary:
                    await telegram_bot.sendMessage(summary)
                last_snapshot = snapshot
            retries = 0
            if timeout is None:
                return
            await asyncio.sleep(timeout)
        except Exception as exc:
            retries += 1
            print(f"[code4rena] error while refreshing data: {exc}")
            traceback.print_exc()
            if retries >= MAX_RETRIES:
                raise RuntimeError("Exceeded maximum retries") from exc
            await asyncio.sleep(retry_delay)

    raise RuntimeError("Exceeded maximum retries")




def _build_notification_summary(report, handle: str | None) -> str:
    base = (
        f"Code4rena {report.contest_id}: "
        f"{report.total_valid_findings}/{report.total_primary} valid primaries | "
        f"judged {report.total_judged}/{report.total_submissions}"
    )
    if report.prize_pool > 0:
        base += f" | pool ${report.prize_pool:,.0f} | pts {report.total_points:.2f}"
    if handle:
        base += f" | {handle}: {report.my_valid_findings} valid"
        if report.prize_pool > 0:
            base += f", est ${report.my_reward:,.2f}"
    elif report.prize_pool > 0 and report.my_reward:
        base += f" | My est reward: ${report.my_reward:,.2f}"
    return base


def main_sync():
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()

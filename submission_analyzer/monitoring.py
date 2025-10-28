from __future__ import annotations

import os

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration


def setup_sentry():
    """
    Configure Sentry to capture crash-level errors when a DSN is provided.
    The integration is a no-op when the SENTRY_DSN environment variable is blank.
    """
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        integrations=[AsyncioIntegration()],
        traces_sample_rate=0.0,
        send_default_pii=False,
    )

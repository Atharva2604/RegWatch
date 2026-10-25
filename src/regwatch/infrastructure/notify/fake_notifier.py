"""Notification infrastructure: SMTP and in-memory collectors."""

import logging
from regwatch.domain.models import Alert
from regwatch.domain.ports import Notifier

logger = logging.getLogger(__name__)


class FakeNotifier(Notifier):
    """In-memory alert collector for unit testing and local developer runs."""

    def __init__(self) -> None:
        self.sent_alerts: list[dict] = []

    def send_alert(self, alert: Alert, subject: str, body: str) -> bool:
        self.sent_alerts.append({
            "alert_id": alert.id,
            "channel": alert.channel,
            "dedupe_key": alert.dedupe_key,
            "subject": subject,
            "body": body,
        })
        logger.info("[NOTIFICATION DISPATCHED] Subject: '%s' to Channel: '%s'", subject, alert.channel)
        return True

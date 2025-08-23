from pathlib import Path
from typing import Any, Dict

import logging
from email.message import EmailMessage

from src.Helpers.config import get_settings

try:
    import aiosmtplib
except Exception:  # pragma: no cover - if package missing we'll log and use dummy
    aiosmtplib = None  # type: ignore


# get the parent directory
BASE_DIR = Path(__file__).resolve().parent


settings = get_settings()


def create_message(recipients: list[str], subject: str, body: str) -> Dict[str, Any]:
    """Return a simple dict message compatible with existing callers.

    The existing code calls `create_message(...)` and passes the result to
    `mail.send_message(...)`. We'll keep that contract: a dict containing
    recipients, subject and body.
    """
    return {"recipients": recipients, "subject": subject, "body": body, "subtype": "html"}


class SMTPMailer:
    def __init__(self, settings: Any):
        self.settings = settings
        self._available = aiosmtplib is not None

    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message dict built by `create_message` using aiosmtplib.

        If aiosmtplib is not installed or MAIL settings are missing, logs a warning
        and returns without raising to avoid disrupting signup flows.
        """
        if not self._available:
            logging.warning("aiosmtplib not installed; skipping email send. Message=%s", message)
            return

        recipients = message.get("recipients")
        subject = message.get("subject")
        body = message.get("body")

        email = EmailMessage()
        email["From"] = self.settings.MAIL_FROM
        email["To"] = ", ".join(recipients) if isinstance(recipients, (list, tuple)) else str(recipients)
        email["Subject"] = subject
        email.set_content(body, subtype="html")

        try:
            await aiosmtplib.send(
                email,
                hostname=self.settings.MAIL_SERVER,
                port=int(getattr(self.settings, "MAIL_PORT", 587)),
                username=getattr(self.settings, "MAIL_USERNAME", None),
                password=getattr(self.settings, "MAIL_PASSWORD", None),
                start_tls=True,
            )
            logging.info("Email sent to %s", recipients)
        except Exception as exc:  # pragma: no cover - runtime SMTP errors
            logging.warning("Failed to send email: %s", exc)


# instantiate mailer
mail = SMTPMailer(settings)




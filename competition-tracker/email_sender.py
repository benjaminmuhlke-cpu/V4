"""Send the report to myself via Gmail SMTP (stdlib smtplib - no need for a
third-party mailer for one HTML email + one attachment).
"""

from __future__ import annotations

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587


def send_report_email(
    sender_address: str,
    app_password: str,
    recipient: str,
    subject: str,
    html_body: str,
    attachment_path: Path,
) -> None:
    msg = MIMEMultipart()
    msg["From"] = sender_address
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    attachment_path = Path(attachment_path)
    with attachment_path.open("rb") as f:
        part = MIMEApplication(f.read(), Name=attachment_path.name)
    part["Content-Disposition"] = f'attachment; filename="{attachment_path.name}"'
    msg.attach(part)

    with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as server:
        server.starttls()
        server.login(sender_address, app_password)
        server.send_message(msg)

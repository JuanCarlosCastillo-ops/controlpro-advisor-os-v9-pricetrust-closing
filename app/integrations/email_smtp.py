from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Iterable


def is_enabled() -> bool:
    return os.getenv("SMTP_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


def send_email(to: Iterable[str], subject: str, body: str) -> dict:
    if not is_enabled():
        return {"enabled": False, "sent": False, "note": "SMTP desactivado. Configurar SMTP_ENABLED=true."}
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL")
    from_name = os.getenv("SMTP_FROM_NAME", "ControlPro Advisor OS")
    missing = [k for k, v in {"SMTP_HOST": host, "SMTP_USER": user, "SMTP_PASSWORD": password, "SMTP_FROM_EMAIL": from_email}.items() if not v]
    if missing:
        raise RuntimeError("Faltan variables SMTP: " + ", ".join(missing))
    msg = EmailMessage()
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)
    return {"enabled": True, "sent": True, "recipients": list(to)}

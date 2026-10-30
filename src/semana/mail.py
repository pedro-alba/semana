import logging
import os
import smtplib
from email.message import EmailMessage


def send(to, subject, text):
    host = os.environ.get("SEMANA_SMTP_HOST")
    if not host:
        logging.getLogger("semana").info("E-mail to %s\nSubject: %s\n\n%s", to, subject, text)
        return
    msg = EmailMessage()
    msg["From"] = os.environ.get("SEMANA_SMTP_FROM", "")
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    with smtplib.SMTP(host, int(os.environ.get("SEMANA_SMTP_PORT") or 587)) as smtp:
        smtp.starttls()
        if os.environ.get("SEMANA_SMTP_USER"):
            smtp.login(os.environ["SEMANA_SMTP_USER"], os.environ.get("SEMANA_SMTP_PASSWORD", ""))
        smtp.send_message(msg)

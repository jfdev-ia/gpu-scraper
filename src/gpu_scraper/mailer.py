"""Send the report by email. The settings come from the .env file."""
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def send_email(subject: str, html_body: str, text_body: str = "Open this email in HTML view.") -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = os.environ.get("MAIL_FROM", user)
    message["To"] = os.environ.get("MAIL_TO", user)
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    if port == 465:  # encrypted from the first byte
        with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
            smtp.login(user, password)
            smtp.send_message(message)
    else:  # usually 587: connect, then switch to encryption
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(message)


if __name__ == "__main__":
    send_email("Test from gpu-scraper", "<p>The email settings <b>work</b>.</p>")
    print("test email sent to", os.environ.get("MAIL_TO", os.environ["SMTP_USER"]))
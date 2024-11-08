import smtplib
from email.message import EmailMessage
from core.logging import logger
from config.env import Env
from fastapi_mail import ConnectionConfig, FastMail

def getFastMailClient_gmail():
    return FastMail(
        config=ConnectionConfig(
            MAIL_USERNAME=Env.GMAIL_SENDER_EMAIL,
            MAIL_PASSWORD=Env.GMAIL_SENDER_PASSWORD,
            MAIL_FROM=Env.GMAIL_SENDER_EMAIL,
            MAIL_PORT=587,
            MAIL_SERVER="smtp.gmail.com",
            MAIL_FROM_NAME="Quickmart",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=False
        )
    )

class EmailClient:
    smtp_connection: smtplib.SMTP = None
    smtp_server = None
    port = None
    username = None
    password = None

    @classmethod
    def init(cls, smtp_server: str, port: str, username: str, password: str):
        cls.smtp_server = smtp_server
        cls.port = port
        cls.username = username
        cls.password = password
        cls.smtp_connection = smtplib.SMTP(cls.smtp_server, cls.port)

        cls.connect()

    @classmethod
    def connect(cls):
        logger.debug(f"Connecting to {cls.smtp_server}:{cls.port}")
        cls.smtp_connection.connect(cls.smtp_server, cls.port)
        try:
            cls.smtp_connection.starttls()
        except Exception as e:
            logger.warning(f"failed to start tls: {e}")

        try:
            cls.smtp_connection.ehlo()
        except Exception as e:
            logger.warning(f"failed to ehlo: {e}")

        logger.debug(
            f"login to {cls.username}:{'*' * len(cls.password)}({len(cls.password)})"
        )
        try:
            cls.smtp_connection.login(cls.username, cls.password)
        except Exception as e:
            logger.warning(f"failed to login: {e}")

    @classmethod
    def reconnect(cls):
        cls.close()
        cls.connect()

    @classmethod
    def send_email(cls, subject, body, recipient):
        msg = EmailMessage()
        msg["From"] = cls.username
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            cls.smtp_connection.send_message(msg)
        except smtplib.SMTPServerDisconnected as e:
            logger.error(
                f"Error sending email: {e}; Reconnecting then resending email"
            )
            cls.connect()
            cls.send_email(subject, body, recipient)
        except (smtplib.SMTPException, smtplib.SMTPServerDisconnected) as e:
            logger.error(
                f"Error sending email: {e}; Reconnecting before raising exception"
            )
            cls.connect()
            raise e

        logger.debug(f"Email sent successfully to {recipient}!")

    @classmethod
    def close(cls):
        if cls.smtp_connection:
            try:
                cls.smtp_connection.quit()
            except Exception as e:
                logger.warning(e)

class GmailEmailClient(EmailClient):
    @classmethod
    def init(cls):
        super().init(
            smtp_server="smtp.gmail.com",
            port="587",
            username=Env.GMAIL_SENDER_EMAIL,
            password=Env.GMAIL_SENDER_PASSWORD,
        )

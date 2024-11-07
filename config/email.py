import smtplib
from email.message import EmailMessage
from core.logging import logger
from config.env import Env


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

        cls.connect()

    @classmethod
    def connect(cls):
        logger.debug(f"Connecting to {cls.smtp_server}:{cls.port}")
        cls.smtp_connection = smtplib.SMTP(cls.smtp_server, cls.port)
        cls.smtp_connection.starttls()

        logger.debug(
            f"login to {cls.username}:{'*' * len(cls.password)}({len(cls.password)})"
        )
        cls.smtp_connection.login(cls.username, cls.password)

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
            if not cls.smtp_connection:
                cls.connect()
            cls.smtp_connection.send_message(msg)
        except (smtplib.SMTPException, smtplib.SMTPServerDisconnected) as e:
            logger.error(
                f"Error sending email: {e}; Reconnecting before raising exception"
            )
            cls.reconnect()
            raise e

        logger.debug(f"Email sent successfully to {recipient}!")

    @classmethod
    def close(cls):
        if cls.smtp_connection:
            cls.smtp_connection.quit()
            cls.smtp_connection = None


class GmailEmailClient(EmailClient):
    @classmethod
    def init(cls):
        super().init(
            smtp_server="smtp.gmail.com",
            port="587",
            username=Env.GMAIL_SENDER_EMAIL,
            password=Env.GMAIL_SENDER_PASSWORD,
        )

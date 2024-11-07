from config.email import GmailEmailClient
from fastapi import Depends

class EmailUtil:
    def __init__(self, gmail_email_client: GmailEmailClient = Depends()):
        self.gmail_email_client = gmail_email_client

    def send_email(self, subject: str, body: str, recipient: str):
        if "@gmail" in recipient:
            self.gmail_email_client.send_email(subject, body, recipient)
        else:
            raise ValueError(f"email not supported")
from config.email import GmailEmailClient, getFastMailClient_gmail
from fastapi_mail import FastMail, MessageSchema, MessageType
from fastapi import Depends
from typing import Union, Literal


class EmailUtil:
    def __init__(self, fm_gmail_client: FastMail = Depends(getFastMailClient_gmail)):
        self.fm_gmail_client = fm_gmail_client

    async def send_email(
        self,
        subject: str,
        body: str,
        recipient: Union[str, list[str]],
        type: Literal["html", "plain"] = "plain",
    ):
        message = MessageSchema(
            subject=subject,
            recipients=recipient if isinstance(recipient, list) else [recipient],
            body=body,
            subtype=type,
        )
        if "@gmail" in recipient:
            await self.fm_gmail_client.send_message(message)
        else:
            raise ValueError(f"email not supported")

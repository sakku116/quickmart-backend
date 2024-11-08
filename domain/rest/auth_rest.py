from dataclasses import dataclass

from fastapi import Form
from pydantic import BaseModel, field_validator

from domain.dto import auth_dto

from .generic_resp import RespData


class BaseTokenResp(BaseModel):
    """
    !!IMPORTANT!!
    fastapi oauth need `access_token` field in the root of the response,
    also my mobile client GUY need it inside of the `data` field.
    so this base token resp model need to be inherited to response model and passed in `data` field at the same time
    """
    access_token: str
    refresh_token: str


@dataclass
class LoginReq:
    username: str = Form()
    password: str = Form()


class LoginResp(RespData, BaseTokenResp):
    pass


@dataclass
class RefreshTokenReq:
    refresh_token: str = Form()


class RefreshTokenResp(RespData, BaseTokenResp):
    pass


@dataclass
class RegisterReq:
    fullname: str = Form()
    username: str = Form()
    email: str = Form()
    password: str = Form()
    confirm_password: str = Form()


class RegisterResp(RespData, BaseTokenResp):
    pass


@dataclass
class CheckTokenReq:
    access_token: str = Form()


class CheckTokenRespData(auth_dto.CurrentUser):
    pass

@dataclass
class VerifyEmailOTPReq:
    otp_code: str = Form()

@dataclass
class SendEmailForgotPasswordOTPReq:
    email: str = Form()

@dataclass
class VerifyForgotPasswordOTPReq:
    email: str = Form()
    otp_code: str = Form()

class VerifyForgotPasswordOTPRespData(BaseModel):
    otp_id: str = ""

@dataclass
class ChangeForgottenPasswordReq:
    otp_id: str = Form()
    new_password: str = Form()
    confirm_password: str = Form()

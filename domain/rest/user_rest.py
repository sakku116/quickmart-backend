from dataclasses import dataclass
from typing import Optional

from fastapi import File, Form, UploadFile
from pydantic import BaseModel

from domain.dto import auth_dto
from domain.model import user_model


class GetMeRespData(auth_dto.CurrentUser):
    pass


@dataclass
class UpdateProfileReq:
    fullname: Optional[str] = Form(None)
    username: Optional[str] = Form(None)
    email: Optional[str] = Form(None)
    phone_number: Optional[str] = Form(None)
    gender: Optional[str] = Form(None)
    birth_date: Optional[str] = Form(None, description="format: DD-MM-YYYY")

class UpdateProfileRespData(user_model.PublicUserModel):
    pass

@dataclass
class UpdatePasswordReq:
    new_password: str = Form(...)
    confirm_password: str = Form(...)

class UpdatePasswordRespData(user_model.PublicUserModel):
    pass

@dataclass
class UpdateProfilePictReq:
    profile_picture: File = UploadFile(...)

class UpdateProfilePictRespData(user_model.PublicUserModel):
    pass

@dataclass
class CheckPasswordReq:
    password: str = Form(...)
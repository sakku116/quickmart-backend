from .base_model import MyBaseModel, _MyBaseModel_Index
from pydantic import field_validator, ValidationError
from typing import Literal, Optional
from datetime import datetime
from pydantic import BaseModel

USER_GENDER_ENUMS = Literal["male", "female"]
USER_GENDER_ENUMS_DEFAULT = "male"

class PublicUserModel(BaseModel):
    id: str
    role: Literal["seller", "customer"] = "customer"
    fullname: str = ""
    username: str = ""
    email: str = ""
    phone_number: str = ""
    gender: Literal[USER_GENDER_ENUMS] = "male"
    birth_date: Optional[str] = None # DD-MM-YYYY
    profile_picture: str = "" # fileanme

    last_active: int = 0

    @field_validator("birth_date", mode="before")
    def birth_date_validator(cls, v):
        if not v:
            return v

        try:
            datetime.strptime(v, "%d-%m-%Y")
            return v
        except Exception as e:
            raise ValidationError("birth_date is not valid")

class UserModel(MyBaseModel, PublicUserModel):
    _coll_name = "users"
    _bucket_name: str = "users"
    _custom_indexes = [
        _MyBaseModel_Index(keys=[("username", -1)], unique=True),
        _MyBaseModel_Index(keys=[("email", -1)], unique=True),
    ]
    _custom_int64_fields = ["last_active"]

    password: str = ""
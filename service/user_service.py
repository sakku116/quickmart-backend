from fastapi import Depends
from domain.model import user_model
from repository import user_repo
from domain.dto import auth_dto
from core.logging import logger
from domain.rest import user_rest
from core.exceptions.http import CustomHttpException
from utils import bcrypt as bcrypt_utils
from pydantic import ValidationError
from datetime import datetime


class UserService:
    def __init__(self, user_repo: user_repo.UserRepo = Depends()) -> None:
        self.user_repo = user_repo

    def getMe(self, current_user: auth_dto.CurrentUser) -> user_rest.GetMeRespData:
        return user_rest.GetMeRespData(**current_user.model_dump())

    def updateProfile(
        self, user_id: str, payload: user_rest.UpdateProfileReq
    ) -> user_rest.UpdateProfileRespData:
        user = self.user_repo.getById(id=user_id)
        if not user:
            exc = CustomHttpException(status_code=404, message="User not found")
            logger.error(exc)
            raise exc

        # validate username
        if payload.username != None:
            _user = self.user_repo.getByUsername(username=payload.username)
            if _user and _user.id != user.id:
                exc = CustomHttpException(
                    status_code=400, message="Username is already taken"
                )
                logger.error(exc)
                raise exc

            if " " in payload.username:
                exc = CustomHttpException(
                    status_code=400, message="Username must not contain spaces"
                )
                logger.error(exc)
                raise exc

        # validate email
        if payload.email != None:
            _user = self.user_repo.getByEmail(email=payload.email)
            if _user and _user.id != user.id:
                exc = CustomHttpException(
                    status_code=400, message="Email is already taken"
                )
                logger.error(exc)
                raise exc

            if "@" not in payload.email:
                exc = CustomHttpException(
                    status_code=400, message="Invalid email address"
                )
                logger.error(exc)
                raise exc

        # validate birth_date
        if payload.birth_date != None:
            try:
                datetime.strptime(payload.birth_date, "%d-%m-%Y")
            except Exception as e:
                exc = CustomHttpException(
                    status_code=400,
                    message="Invalid birth date, format should be DD-MM-YYYY",
                )
                logger.error(exc)
                raise exc

        # update fields
        if payload.fullname != None:
            user.fullname = payload.fullname

        if payload.username != None:
            user.username = payload.username

        if payload.email != None:
            user.email = payload.email

        if payload.phone_number != None:
            user.phone_number = payload.phone_number

        if payload.gender != None:
            user.gender = payload.gender

        if payload.birth_date != None:
            user.birth_date = payload.birth_date

        # re-validate user
        user.model_validate()  # dont need to raise exception because ValidationError automatically handled by exceptions handler

        # update user
        user.updated_at = datetime.now()
        user.updated_by = user_id
        self.user_repo.update(id=user.id, data=user)

        return user_rest.UpdateProfileRespData(**user.model_dump())

    def checkPassword(self, user_id: str, payload: user_rest.CheckPasswordReq) -> bool:
        user = self.user_repo.getById(id=user_id)
        if not user:
            exc = CustomHttpException(status_code=404, message="User not found")
            logger.error(exc)
            raise exc

        is_pw_match = bcrypt_utils.checkPassword(payload.password, user.password)
        if not is_pw_match:
            exc = CustomHttpException(status_code=400, message="Invalid password")
            logger.error(exc)
            raise exc

        return True

    def updatePassword(
        self, user_id: str, payload: user_rest.UpdatePasswordReq
    ) -> user_rest.UpdatePasswordRespData:
        user = self.user_repo.getById(id=user_id)
        if not user:
            exc = CustomHttpException(status_code=404, message="User not found")
            logger.error(exc)
            raise exc

        # validate
        if len(payload.new_password) < 7:
            exc = CustomHttpException(
                status_code=400,
                message="New password must be at least 7 characters long",
            )
            logger.error(exc)
            raise exc

        if " " in payload.new_password:
            exc = CustomHttpException(
                status_code=400, message="New password must not contain spaces"
            )
            logger.error(exc)
            raise exc

        if payload.new_password != payload.confirm_password:
            exc = CustomHttpException(
                status_code=400,
                message="New password and confirm password does not match",
            )
            logger.error(exc)
            raise exc

        # update user
        user.updated_at = datetime.now()
        user.updated_by = user_id
        user.password = bcrypt_utils.hashPassword(payload.new_password)
        self.user_repo.update(id=user.id, data=user)

        return user_rest.UpdatePasswordRespData(**user.model_dump())

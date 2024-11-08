from fastapi import Depends
from domain.model import user_model
from pydantic import ValidationError
from repository import user_repo, refresh_token_repo, otp_repo
from domain.dto import auth_dto
from core.logging import logger
from domain.rest import user_rest
from core.exceptions.http import CustomHttpException
from utils import bcrypt as bcrypt_utils
from utils import helper


class UserService:
    def __init__(
        self,
        user_repo: user_repo.UserRepo = Depends(),
        refresh_token_repo: refresh_token_repo.RefreshTokenRepo = Depends(),
        otp_repo: otp_repo.OtpRepo = Depends(),
    ) -> None:
        self.user_repo = user_repo
        self.otp_repo = otp_repo
        self.refresh_token_repo = refresh_token_repo

    def getMe(self, current_user: auth_dto.CurrentUser) -> user_rest.GetMeRespData:
        return user_rest.GetMeRespData(**current_user.model_dump())

    def updateProfile(
        self, user_id: str, payload: user_rest.UpdateProfileReq
    ) -> user_rest.UpdateProfileRespData:
        logger.debug(f"payload: {payload}")
        user = self.user_repo.getById(id=user_id)
        if not user:
            exc = CustomHttpException(status_code=404, message="User not found")
            logger.error(exc)
            raise exc

        # update fields
        if payload.fullname != None:
            user.fullname = payload.fullname

        if payload.username != None:
            user.username = payload.username

        if payload.email != None:
            user.email = payload.email
            user.email_verified = False

        if payload.phone_number != None:
            user.phone_number = payload.phone_number

        if payload.gender != None:
            user.gender = payload.gender

        if payload.birth_date != None:
            user.birth_date = payload.birth_date

        if payload.language != None:
            user.language = payload.language

        if payload.currency != None:
            user.currency = payload.currency

        # re-validate user
        try:
            user.model_validate(
                user
            )
        except ValidationError as e:
            for error in e.errors():
                exc = CustomHttpException(
                    status_code=400,
                    message=error.get("msg") or "Invalid value",
                    detail=e.json(),
                )
                logger.error(exc)
                raise exc

        # update user
        user.updated_at = helper.timeNowEpoch()
        user.updated_by = user_id
        user = self.user_repo.update(id=user.id, data=user)
        logger.debug(f"updated_user: {user}")
        if not user:
            exc = CustomHttpException(status_code=500, message="Failed to update user")
            logger.error(exc)
            raise exc

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
        user.updated_at = helper.timeNowEpoch()
        user.updated_by = user_id
        user.password = bcrypt_utils.hashPassword(payload.new_password)
        self.user_repo.update(id=user.id, data=user)

        return user_rest.UpdatePasswordRespData(**user.model_dump())

    def delete(self, user_id: str):
        _params = {"user_id": user_id}

        user = self.user_repo.delete(id=user_id)
        if not user:
            exc = CustomHttpException(
                status_code=404, message="User not found", context=_params
            )
            logger.error(exc)
            raise exc

        self.refresh_token_repo.deleteManyByCreatedBy(created_by=user_id)
        self.otp_repo.deleteManyByCreatedBy(created_by=user_id)

        return
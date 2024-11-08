from dataclasses import asdict
from datetime import datetime, timedelta
from pydantic import ValidationError
from typing import Callable, Literal

import jwt
from fastapi import Depends

from config.env import Env
from core.exceptions.http import CustomHttpException
from core.logging import logger
from domain.dto import auth_dto
from domain.model import otp_model, refresh_token_model, user_model
from domain.rest import auth_rest
from repository import otp_repo, refresh_token_repo, user_repo
from utils import bcrypt as bcrypt_utils
from utils import helper
from utils import jwt as jwt_utils
from utils.service import email_util


class AuthService:
    def __init__(
        self,
        user_repo: user_repo.UserRepo = Depends(),
        refresh_token_repo: refresh_token_repo.RefreshTokenRepo = Depends(),
        email_util: email_util.EmailUtil = Depends(),
        otp_repo: otp_repo.OtpRepo = Depends(),
    ):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo
        self.email_util = email_util
        self.otp_repo = otp_repo

    def login(self, payload: auth_rest.LoginReq) -> auth_rest.LoginResp:
        # check if input is email
        is_email = "@" in payload.username

        # check user if exist by email or username
        if is_email:
            user = self.user_repo.getByEmail(email=payload.username)
        else:
            user = self.user_repo.getByUsername(username=payload.username)

        if not user:
            exc = CustomHttpException(status_code=401, message="User not found")
            logger.error(exc)
            raise exc

        # check password
        is_pwd_match = bcrypt_utils.checkPassword(
            input_pw=payload.password, hashed_pw=user.password
        )
        if not is_pwd_match:
            exc = CustomHttpException(status_code=401, message="Invalid password")
            logger.error(exc)
            raise exc

        # generate jwt token
        jwt_payload = auth_dto.JwtPayload(
            **user.model_dump(),
            sub=user.id,
            exp=datetime.utcnow() + timedelta(hours=Env.TOKEN_EXPIRES_HOURS),
        )
        jwt_token = jwt_utils.encodeToken(
            payload=jwt_payload.model_dump(), secret=Env.JWT_SECRET_KEY
        )

        # generate refresh token
        time_now = helper.timeNowEpoch()
        new_refresh_token = refresh_token_model.RefreshTokenModel(
            id=helper.generateUUID4(),
            created_at=time_now,
            created_by=user.id,
            expired_at=int(
                (
                    datetime.utcnow() + timedelta(hours=Env.REFRESH_TOKEN_EXPIRES_HOURS)
                ).timestamp()
            ),
        )
        self.refresh_token_repo.create(data=new_refresh_token)

        return auth_rest.LoginResp(
            access_token=jwt_token,
            refresh_token=new_refresh_token.id,
        )

    def refreshToken(
        self, payload: auth_rest.RefreshTokenReq
    ) -> auth_rest.RefreshTokenResp:
        # find refresh token
        refresh_token = self.refresh_token_repo.getById(id=payload.refresh_token)
        if not refresh_token:
            exc = CustomHttpException(
                status_code=401, message="Refresh token not found"
            )
            logger.error(exc)
            raise exc

        # check if expired
        if refresh_token.expired_at < helper.timeNowEpoch():
            exc = CustomHttpException(status_code=401, message="Refresh token expired")
            logger.error(exc)

        # get user
        user = self.user_repo.getById(id=refresh_token.created_by)
        if not user:
            exc = CustomHttpException(status_code=401, message="User not found")
            logger.error(exc)
            raise exc

        # generate jwt token
        jwt_payload = auth_dto.JwtPayload(
            **user.model_dump(),
            sub=user.id,
            exp=datetime.utcnow() + timedelta(hours=Env.TOKEN_EXPIRES_HOURS),
        )
        jwt_token = jwt_utils.encodeToken(
            payload=jwt_payload.model_dump(), secret=Env.JWT_SECRET_KEY
        )

        # delete current refresh token
        self.refresh_token_repo.delete(id=payload.refresh_token)

        # generate new refresh token
        time_now = helper.timeNowEpoch()
        new_refresh_token = refresh_token_model.RefreshTokenModel(
            id=helper.generateUUID4(),
            created_at=time_now,
            created_by=user.id,
            expired_at=int(
                (
                    datetime.utcnow() + timedelta(hours=Env.REFRESH_TOKEN_EXPIRES_HOURS)
                ).timestamp()
            ),
        )
        self.refresh_token_repo.create(data=new_refresh_token)

        return auth_rest.RefreshTokenResp(
            access_token=jwt_token,
            refresh_token=new_refresh_token.id,
        )

    def verifyToken(self, token: str) -> auth_dto.CurrentUser:
        # decode token
        claims = None
        try:
            claims = auth_dto.JwtPayload(
                **jwt_utils.decodeToken(token, Env.JWT_SECRET_KEY)
            )
        except jwt.ExpiredSignatureError:
            exc = CustomHttpException(status_code=401, message="Token expired")
            logger.error(exc)
            raise exc
        except jwt.InvalidTokenError:
            exc = CustomHttpException(status_code=401, message="Invalid token")
            logger.error(exc)
            raise exc
        except Exception as e:
            exc = CustomHttpException(
                status_code=401, message="Invalid token", detail=str(e)
            )
            logger.error(exc)
            raise exc

        # update last_active
        time_now = helper.timeNowEpoch()
        user = self.user_repo.updateLastActive(id=claims.sub, last_active=time_now)
        if not user:
            exc = CustomHttpException(status_code=401, message="User not found")
            logger.error(exc)
            raise exc

        result = auth_dto.CurrentUser(**user.model_dump())

        return result

    def checkToken(
        self, payload: auth_rest.CheckTokenReq
    ) -> auth_rest.CheckTokenRespData:
        data = self.verifyToken(token=payload.access_token.removeprefix("Bearer "))
        return auth_rest.CheckTokenRespData(**data.model_dump())

    def register(self, payload: auth_rest.RegisterReq) -> auth_rest.RegisterResp:
        # validate password
        if len(payload.password) < 6:
            exc = CustomHttpException(
                status_code=400, message="Password must be at least 7 characters long"
            )
            logger.error(exc)
            raise exc

        if " " in payload.password:
            exc = CustomHttpException(
                status_code=400, message="Password must not contain spaces"
            )
            logger.error(exc)
            raise exc

        # validate password confirmation
        if payload.password != payload.confirm_password:
            exc = CustomHttpException(
                status_code=400, message="Password does not match"
            )
            logger.error(exc)
            raise exc

        # check if email already exist
        if self.user_repo.getByEmail(email=payload.email):
            exc = CustomHttpException(status_code=400, message="Email already exist")
            logger.error(exc)
            raise exc

        # check if username already exist
        if self.user_repo.getByUsername(username=payload.username):
            exc = CustomHttpException(status_code=400, message="Username already exist")
            logger.error(exc)
            raise exc

        # hash password
        hashed_pw = bcrypt_utils.hashPassword(payload.password)

        # create user
        time_now = helper.timeNowEpoch()
        try:
            new_user = user_model.UserModel(
                id=helper.generateUUID4(),
                created_at=time_now,
                fullname=payload.fullname,
                username=payload.username,
                email=payload.email,
                password=hashed_pw,
                role="customer",
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

        self.user_repo.create(data=new_user)

        # generate jwt token
        jwt_payload = auth_dto.JwtPayload(
            **new_user.model_dump(),
            sub=new_user.id,
            exp=datetime.utcnow() + timedelta(hours=Env.TOKEN_EXPIRES_HOURS),
        )
        jwt_token = jwt_utils.encodeToken(
            payload=jwt_payload.model_dump(), secret=Env.JWT_SECRET_KEY
        )

        # generate new refresh token
        time_now = helper.timeNowEpoch()
        new_refresh_token = refresh_token_model.RefreshTokenModel(
            id=helper.generateUUID4(),
            created_at=time_now,
            created_by=new_user.id,
            expired_at=int(
                (
                    datetime.utcnow() + timedelta(hours=Env.REFRESH_TOKEN_EXPIRES_HOURS)
                ).timestamp()
            ),
        )
        self.refresh_token_repo.create(data=new_refresh_token)

        result = auth_rest.RegisterResp(
            access_token=jwt_token,
            refresh_token=new_refresh_token.id,
        )
        return result

    async def sendVerifyEmailOTP(self, current_user: auth_dto.CurrentUser):
        # check if email already verified
        if current_user.email_verified:
            exc = CustomHttpException(status_code=400, message="Email already verified")
            logger.error(exc)
            raise exc

        # check if any active otp exist
        otp = self.otp_repo.getUnverifiedByCreatedBy(created_by=current_user.id)
        if otp:
            # delete
            self.otp_repo.delete(id=otp.id)

        # create new otp
        time_now = helper.timeNowEpoch()
        new_otp = otp_model.OtpModel(
            id=helper.generateUUID4(),
            created_at=time_now,
            created_by=current_user.id,
            code=helper.generateRandomNumber(length=6),
        )

        self.otp_repo.create(data=new_otp)

        # check current user's email
        if not current_user.email:
            exc = CustomHttpException(
                status_code=400,
                message="User email not configured, please update your profile",
            )
            logger.error(exc)
            raise exc

        # send email
        try:
            await self.email_util.send_email(
                subject="Quickmart Email Verification",
                body=f"Your OTP is {new_otp.code}",
                recipient=current_user.email,
            )
        except Exception as e:
            exc = CustomHttpException(
                status_code=500, message="Failed to send email", detail=str(e)
            )
            logger.error(exc)
            raise exc

    def verifyEmailOTP(
        self, current_user: auth_dto.CurrentUser, payload: auth_rest.VerifyEmailOTPReq
    ):
        _params = {
            "current_user.id": current_user.id,
        }

        otp = self.otp_repo.getLatestByCreatedBy(created_by=current_user.id)
        if not otp:
            exc = CustomHttpException(
                status_code=400, message="OTP not found", context=_params
            )
            logger.error(exc)
            raise exc

        if helper.isExpired(otp.created_at, expr_seconds=Env.OTP_EXPIRES_SECONDS):
            exc = CustomHttpException(
                status_code=400, message="OTP expired", context=_params
            )
            logger.error(exc)
            raise exc

        if payload.otp_code != otp.code:
            exc = CustomHttpException(
                status_code=400, message="Invalid OTP", context=_params
            )
            logger.error(exc)
            raise exc

        # delete otp
        self.otp_repo.delete(id=otp.id)

        # update user's email verified
        user = self.user_repo.getById(id=current_user.id)
        if not user:
            exc = CustomHttpException(
                status_code=404, message="User not found", context=_params
            )
            logger.error(exc)
            raise exc

        user.email_verified = True
        user.updated_at = helper.timeNowEpoch()
        self.user_repo.update(id=user.id, data=user)

    async def sendEmailForgotPasswordOTP(
        self, payload: auth_rest.SendEmailForgotPasswordOTPReq
    ):
        # check if email is registered
        user = self.user_repo.getByEmail(email=payload.email)
        if not user:
            exc = CustomHttpException(status_code=400, message="Email not registered")
            logger.error(exc)
            raise exc

        # check if any unverified otp exist
        otp = self.otp_repo.getUnverifiedByCreatedBy(created_by=user.id)
        if otp:
            # delete
            self.otp_repo.delete(id=otp.id)

        # create new otp
        time_now = helper.timeNowEpoch()
        new_otp = otp_model.OtpModel(
            id=helper.generateUUID4(),
            created_at=time_now,
            created_by=user.id,
            code=helper.generateRandomNumber(length=6),
        )

        self.otp_repo.create(data=new_otp)

        # send email
        try:
            await self.email_util.send_email(
                subject="Quickmart New Password Verification",
                body=f"Your OTP is {new_otp.code}",
                recipient=payload.email,
            )
        except Exception as e:
            exc = CustomHttpException(
                status_code=500, message="Failed to send email", detail=str(e)
            )
            logger.error(exc)
            raise exc

    def verifyForgotPasswordOTP(
        self, payload: auth_rest.VerifyForgotPasswordOTPReq
    ) -> auth_rest.VerifyForgotPasswordOTPRespData:
        _params = {**asdict(payload)}
        # get users by email
        user = self.user_repo.getByEmail(email=payload.email)
        if not user:
            exc = CustomHttpException(status_code=400, message="Email not found")
            logger.error(exc)
            raise exc

        # get latest by created by
        otp = self.otp_repo.getLatestByCreatedBy(created_by=user.id)
        if not otp:
            exc = CustomHttpException(
                status_code=400, message="OTP not found", context=_params
            )
            logger.error(exc)
            raise exc

        # check if otp is expired
        if helper.isExpired(otp.created_at, expr_seconds=Env.OTP_EXPIRES_SECONDS):
            exc = CustomHttpException(
                status_code=400, message="OTP expired", context=_params
            )
            logger.error(exc)
            raise exc

        # check if otp is valid
        if payload.otp_code != otp.code:
            exc = CustomHttpException(
                status_code=400, message="Invalid OTP", context=_params
            )
            logger.error(exc)
            raise exc

        # mark as verified
        otp.verified = True
        otp.updated_at = helper.timeNowEpoch()
        self.otp_repo.update(id=otp.id, data=otp)

        return auth_rest.VerifyForgotPasswordOTPRespData(otp_id=otp.id)

    def changeForgottenPassword(self, payload: auth_rest.ChangeForgottenPasswordReq):
        otp = self.otp_repo.getById(id=payload.otp_id)
        if not otp:
            exc = CustomHttpException(status_code=400, message="OTP not found")
            logger.error(exc)
            raise exc

        # check if otp is expired
        if helper.isExpired(otp.created_at, expr_seconds=Env.OTP_EXPIRES_SECONDS):
            exc = CustomHttpException(status_code=400, message="OTP expired")
            logger.error(exc)
            raise exc

        # check if otp is verified
        if not otp.verified:
            exc = CustomHttpException(
                status_code=400, message="OTP not verified, verify first"
            )
            logger.error(exc)

        user = self.user_repo.getById(id=otp.created_by)
        if not user:
            exc = CustomHttpException(status_code=400, message="User not found")
            logger.error(exc)
            raise exc

        # validate password
        if len(payload.new_password) < 6:
            exc = CustomHttpException(
                status_code=400, message="Password must be at least 6 characters long"
            )
            logger.error(exc)
            raise exc

        if " " in payload.new_password:
            exc = CustomHttpException(
                status_code=400, message="Password must not contain spaces"
            )
            logger.error(exc)
            raise exc

        if payload.new_password != payload.confirm_password:
            exc = CustomHttpException(
                status_code=400, message="Password confirmation does not match"
            )
            logger.error(exc)
            raise exc

        # update password
        user.password = bcrypt_utils.hashPassword(payload.new_password)
        user.updated_by = user.id
        user.updated_at = helper.timeNowEpoch()
        user = self.user_repo.update(id=user.id, data=user)
        if not user:
            exc = CustomHttpException(
                status_code=500, message="Failed to update password, user not found"
            )
            logger.error(exc)
            raise exc

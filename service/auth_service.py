from datetime import datetime, timedelta

from fastapi import Depends
from jwt import exceptions as jwt_exceptions

from config.env import Env
from core.exceptions.http import CustomHttpException
from core.logging import logger
import jwt
from domain.dto import auth_dto
from domain.model import refresh_token_model, user_model
from domain.rest import auth_rest
from repository import refresh_token_repo, user_repo
from utils import bcrypt as bcrypt_utils
from utils import helper
from utils import jwt as jwt_utils


class AuthService:
    def __init__(
        self,
        user_repo: user_repo.UserRepo = Depends(),
        refresh_token_repo: refresh_token_repo.RefreshTokenRepo = Depends(),
    ):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

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
            exp=datetime.utcnow() + timedelta(hours=Env.TOKEN_EXPIRES_HOURS)
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
            exp=datetime.utcnow() + timedelta(hours=Env.TOKEN_EXPIRES_HOURS)
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
        self.user_repo.updateLastActive(id=claims.sub, last_active=time_now)

        result = auth_dto.CurrentUser(**claims.model_dump())

        return result

    def checkToken(self, payload: auth_rest.CheckTokenReq) -> auth_rest.CheckTokenRespData:
        data = self.verifyToken(token=payload.access_token.removeprefix("Bearer "))
        return auth_rest.CheckTokenRespData(**data.model_dump())

    def register(self, payload: auth_rest.RegisterReq) -> auth_rest.RegisterResp:
        # validate password
        if len(payload.password) < 7:
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

        # validate email
        if "@" not in payload.email:
            exc = CustomHttpException(
                status_code=400, message="Invalid email address"
            )
            logger.error(exc)
            raise exc

        # validate username
        if " " in payload.username:
            exc = CustomHttpException(
                status_code=400, message="Username must not contain spaces"
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
        new_user = user_model.UserModel(
            id=helper.generateUUID4(),
            created_at=time_now,
            fullname=payload.fullname,
            username=payload.username,
            email=payload.email,
            password=hashed_pw,
            role="customer",
        )
        self.user_repo.create(data=new_user)

        # generate jwt token
        jwt_payload = auth_dto.JwtPayload(
            **new_user.model_dump(),
            sub=new_user.id,
            exp=datetime.utcnow() + timedelta(hours=Env.TOKEN_EXPIRES_HOURS)
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

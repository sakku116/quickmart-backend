from fastapi import APIRouter, Depends

from domain.rest import user_rest, generic_resp
from service import user_service
from core.dependencies import verifyToken
from domain.dto import auth_dto

UserRouter = APIRouter(
    prefix="/user",
    tags=["User"],
    dependencies=[Depends(verifyToken)],
)


@UserRouter.get("/me", response_model=generic_resp.RespData[user_rest.GetMeRespData])
def get_me(
    service: user_service.UserService = Depends(),
    current_user: auth_dto.CurrentUser = Depends(verifyToken),
):
    data = service.getMe(current_user=current_user)
    return generic_resp.RespData[user_rest.GetMeRespData](data=data)


@UserRouter.patch(
    "/me/profile",
    response_model=generic_resp.RespData[user_rest.UpdatePasswordRespData],
)
def update_my_profile(
    payload: user_rest.UpdateProfileReq = Depends(),
    service: user_service.UserService = Depends(),
    current_user: auth_dto.CurrentUser = Depends(verifyToken),
):
    data = service.updateProfile(user_id=current_user.id, payload=payload)
    return generic_resp.RespData[user_rest.UpdateProfileRespData](data=data)

@UserRouter.post(
    "/me/check-password",
    response_model=generic_resp.RespData,
)
def check_my_password(
    payload: user_rest.CheckPasswordReq = Depends(),
    service: user_service.UserService = Depends(),
    current_user: auth_dto.CurrentUser = Depends(verifyToken),
):
    service.checkPassword(user_id=current_user.id, payload=payload)
    return generic_resp.RespData()

@UserRouter.patch(
    "/me/password",
    response_model=generic_resp.RespData[user_rest.UpdatePasswordRespData],
)
def update_my_password(
    payload: user_rest.UpdatePasswordReq = Depends(),
    service: user_service.UserService = Depends(),
    current_user: auth_dto.CurrentUser = Depends(verifyToken),
):
    data = service.updatePassword(user_id=current_user.id, payload=payload)
    return generic_resp.RespData[user_rest.UpdatePasswordRespData](data=data)

@UserRouter.delete(
    "/me", response_model=generic_resp.RespData
)
def delete_my_profile(
    service: user_service.UserService = Depends(),
    current_user: auth_dto.CurrentUser = Depends(verifyToken),
):
    service.delete(user_id=current_user.id)
    return generic_resp.RespData()
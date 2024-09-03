from typing_extensions import Annotated
from fastapi import Depends
from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from config.schemas.auth_schema import InputLogin, InputUser, OutputLogin
from config.schemas.common_schema import StandardResponse, TokenData
from src.controllers.auth.controller_auth import AuthController
from src.controllers.service_common import get_current_user


auth_router = APIRouter(prefix="/api/v1", tags=["Auth"])


@auth_router.post("/login")
async def user_login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_controller: AuthController = Depends(),
):
    return await user_controller.login_user(
        InputLogin(
            email=form_data.username,
            password=form_data.password,
        )
    )


@auth_router.post("/register")
async def user_register(
    input_user: InputUser, user_controller: AuthController = Depends()
):
    await user_controller.insert_new_user(input_user)
    return StandardResponse(detail="Success Register User")


@auth_router.get("/profile")
async def user_profile(
    token: Annotated[TokenData, Depends(get_current_user)],
    user_controller: AuthController = Depends(),
):
    return await user_controller.get_current_user(token)


# @auth_router.delete("/delete")
# async def user_delete(
#     id: int,
#     user_controller: AuthController = Depends(),
# ):
#     return await user_controller.delete_user(id)

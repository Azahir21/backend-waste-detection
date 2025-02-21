from typing_extensions import Annotated
from fastapi import Depends, HTTPException, Query
from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from config.schemas.auth_schema import InputLogin, InputUser, OutputLogin
from config.schemas.common_schema import StandardResponse, TokenData
from src.controllers.auth.controller_stackholder_auth import (
    AuthStackholderController as AuthController,
)
from src.controllers.service_common import get_current_user


auth_stackholder_router = APIRouter(
    prefix="/api/v1/stackholder", tags=["Auth_Stackholder"]
)


@auth_stackholder_router.post("/login")
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


@auth_stackholder_router.post("/auth/register")
async def user_register(
    input_user: InputUser, user_controller: AuthController = Depends()
):
    input_user.role = "stackholder"
    await user_controller.insert_new_user(input_user)
    return StandardResponse(detail="Success Register User")


@auth_stackholder_router.get("/profile")
async def user_profile(
    token: Annotated[TokenData, Depends(get_current_user)],
    user_controller: AuthController = Depends(),
):
    return await user_controller.get_current_user(token)


@auth_stackholder_router.put("/deactivate_user")
async def user_deactivate(
    id: int,
    token: Annotated[TokenData, Depends(get_current_user)],
    user_controller: AuthController = Depends(),
):
    try:
        return await user_controller.deactivate_user(token, id)
    except HTTPException as http_ex:
        raise http_ex  # Re-raise HTTP exceptions with their original status codes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@auth_stackholder_router.put("/reset_password")
async def user_reset_password(
    id: int,
    password: str,
    token: Annotated[TokenData, Depends(get_current_user)],
    user_controller: AuthController = Depends(),
):
    try:
        return await user_controller.reset_password(token, id, password)
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@auth_stackholder_router.get("/get_all_user")
async def user_get_all(
    token: Annotated[TokenData, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (default is 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Page size (default is 10, max 100)"
    ),
    sort_by: str = Query(
        "id",
        description="Sort by field. Options: id, fullname, gender, username, email, role, status",
    ),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    search: str = Query(
        "", description="Search query for all fields (empty means no search)"
    ),
    user_controller: AuthController = Depends(),
):
    return await user_controller.get_all_user(
        token, page, page_size, sort_by, sort_order, search
    )


# @auth_stackholder_router.delete("/delete")
# async def user_delete(
#     id: int,
#     user_controller: AuthController = Depends(),
# ):
#     return await user_controller.delete_user(id)

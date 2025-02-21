import asyncio
from fastapi import HTTPException
from fastapi.params import Depends
from src.repositories.repository_user import UserRepository
from src.controllers.auth.service_jwt import JWTService
from src.controllers.auth import service_security
from config.schemas.auth_schema import (
    InputUser,
    InputLogin,
    OutputAllUser,
    OutputLogin,
    OutputProfile,
)
from config.schemas.common_schema import TokenData


class AuthStackholderController:
    def __init__(
        self,
        user_repository: UserRepository = Depends(),
        jwt_service: JWTService = Depends(),
    ):
        self.user_repository = user_repository
        self.jwt_service = jwt_service
        self.security_service = service_security

    async def insert_new_user(self, input_user: InputUser):
        found_duplicate_username = await self.user_repository.find_user_by_username(
            input_user.username
        )

        found_duplicate_email = await self.user_repository.find_user_by_email(
            input_user.email
        )
        if found_duplicate_username:
            raise HTTPException(status_code=404, detail="Username already exists")
        if found_duplicate_email:
            raise HTTPException(status_code=404, detail="Invalid Email or Password")
        input_user.password = self.security_service.get_password_hash(
            input_user.password
        )
        return await self.user_repository.insert_new_user(input_user)

    async def login_user(self, input_login: InputLogin):
        found_user = await self.user_repository.find_user_by_email(input_login.email)
        if found_user is None:
            raise HTTPException(status_code=404, detail="Invalid Email or Password")
        if found_user.active is False:
            raise HTTPException(status_code=404, detail="User is not active")
        if found_user.role == "user":
            raise HTTPException(status_code=404, detail="User is not a stackholder")
        if not self.security_service.verify_password(
            input_login.password,
            found_user.password,
        ):
            raise HTTPException(status_code=404, detail="Invalid Email or Password")
        jwt_token = self.jwt_service.create_access_token(
            TokenData(
                userID=found_user.id.__str__(),
                name=found_user.username,
                role=found_user.role,
            ).dict()
        )
        return OutputLogin(
            access_token=jwt_token,
            token_type="bearer",
            username=found_user.username,
            role=found_user.role,
        )

    async def get_current_user(self, tokenData: TokenData):
        try:
            found_user = await self.user_repository.find_user_by_username(
                tokenData.name
            )
            return OutputProfile(username=found_user.username, email=found_user.email)
        except Exception as e:
            raise HTTPException(status_code=404, detail="Invalid Token")

    async def deactivate_user(self, tokenData: TokenData, id: int):
        # First check user permissions
        found_user = await self.user_repository.find_user_by_username(tokenData.name)
        if found_user.role != "admin":
            raise HTTPException(status_code=403, detail="User is not a Admin")

        # Attempt to deactivate user
        deactivate_user = await self.user_repository.deactivate_user(id)

        # Return success response
        if deactivate_user.active:
            return {
                "detail": f"User with username: {deactivate_user.username} has been activated"
            }
        return {
            "detail": f"User with username: {deactivate_user.username} has been deactivated"
        }

    async def reset_password(self, tokenData: TokenData, id: int, password: str):
        # First check user permissions
        found_user = await self.user_repository.find_user_by_username(tokenData.name)
        if found_user.role != "admin":
            raise HTTPException(status_code=403, detail="User is not a Admin")

        # Attempt to reset password
        password = self.security_service.get_password_hash(password)
        reset_password = await self.user_repository.reset_password(id, password)

        # Return success response
        return {
            "detail": f"Password for user: {reset_password.username} has been reset"
        }

    async def get_all_user(
        self,
        token: TokenData,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
        search: str,
    ):
        # First check user permissions
        found_user = await self.user_repository.find_user_by_username(token.name)
        if found_user.role != "admin":
            raise HTTPException(status_code=403, detail="User is not an Admin")

        # Fetch paginated users with sorting and search
        all_user, total_count = await self.user_repository.get_all_user(
            page, page_size, sort_by, sort_order, search
        )

        # Format the response
        return {
            "users": [
                OutputAllUser(
                    id=user.id,
                    full_name=user.fullName,
                    gender=user.jenisKelamin,
                    username=user.username,
                    email=user.email,
                    role=user.role,
                    status=user.active,
                )
                for user in all_user
            ],
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
        }

    # async def delete_user(self, id: int):
    #     try:
    #         await self.user_repository.delete_user(id)
    #         return {"message": "User Deleted"}
    #     except Exception as e:
    #         raise HTTPException(status_code=404, detail="Invalid Token")

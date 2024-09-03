import asyncio
from fastapi import HTTPException
from fastapi.params import Depends
from src.repositories.repository_user import UserRepository
from src.controllers.auth.service_jwt import JWTService
from src.controllers.auth import service_security
from config.schemas.auth_schema import InputUser, InputLogin, OutputLogin, OutputProfile
from config.schemas.common_schema import TokenData


class AuthController:
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
        print("log")
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
        if not self.security_service.verify_password(
            input_login.password,
            found_user.password,
        ):
            raise HTTPException(status_code=404, detail="Invalid Email or Password")
        jwt_token = self.jwt_service.create_access_token(
            TokenData(
                userID=found_user.id.__str__(),
                name=found_user.username,
            ).dict()
        )
        return OutputLogin(
            access_token=jwt_token,
            token_type="bearer",
            username=found_user.username,
        )

    async def get_current_user(self, tokenData: TokenData):
        try:
            found_user = await self.user_repository.find_user_by_username(
                tokenData.name
            )
            return OutputProfile(username=found_user.username, email=found_user.email)
        except Exception as e:
            raise HTTPException(status_code=404, detail="Invalid Token")

    # async def delete_user(self, id: int):
    #     try:
    #         await self.user_repository.delete_user(id)
    #         return {"message": "User Deleted"}
    #     except Exception as e:
    #         raise HTTPException(status_code=404, detail="Invalid Token")

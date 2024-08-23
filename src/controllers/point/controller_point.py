from fastapi import Depends, HTTPException
from config.schemas.common_schema import TokenData
from config.schemas.point_schema import OutputPoint
from src.repositories.repository_user import UserRepository
from src.repositories.repository_point import PointRepository
from config.models import user_model


class PointController:
    def __init__(
        self,
        point_repository: PointRepository = Depends(),
        user_repository: UserRepository = Depends(),
    ):
        self.point_repository = point_repository
        self.user_repository = user_repository

    async def get_current_user_point(self, token_data: TokenData):
        current_user = await self.user_repository.find_user_by_username(token_data.name)
        if current_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user_point = await self.point_repository.get_current_user_point(current_user.id)
        return OutputPoint(point=user_point.point, updatedAt=user_point.updatedAt)

    async def get_today_point(self, token_data: TokenData):
        current_user = await self.user_repository.find_user_by_username(token_data.name)
        if current_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user_point = await self.point_repository.get_today_point(current_user.id)
        return user_point

    async def get_weekly_point(self, token_data: TokenData):
        current_user = await self.user_repository.find_user_by_username(token_data.name)
        if current_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user_point = (
            await self.point_repository.get_all_users_weekly_points_and_ranking(
                current_user.id
            )
        )
        return user_point

    async def get_monthly_point(self, token_data: TokenData):
        current_user = await self.user_repository.find_user_by_username(token_data.name)
        if current_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user_point = (
            await self.point_repository.get_all_users_monthly_points_and_ranking(
                current_user.id
            )
        )
        return user_point

    async def get_all_user_point(self, token_data: TokenData):
        user = await self.user_repository.find_user_by_username(token_data.name)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return await self.point_repository.get_all_users_points_and_ranking(user.id)

    async def get_all_user_point_timeseries(
        self, token_data: TokenData, start_date: str = None, end_date: str = None
    ):
        user = await self.user_repository.find_user_by_username(token_data.name)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return await self.point_repository.get_all_user_point_timeseries(
            start_date, end_date, user.id
        )

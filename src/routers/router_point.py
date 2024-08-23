from typing_extensions import Annotated
from fastapi import APIRouter, Depends

from config.schemas.common_schema import TokenData
from src.controllers.point.controller_point import PointController
from src.controllers.service_common import get_current_user


point_router = APIRouter(prefix="/api/v1", tags=["Point"])


@point_router.get("/point")
async def get_current_user_point(
    token: Annotated[TokenData, Depends(get_current_user)],
    point_controller: PointController = Depends(),
):
    return await point_controller.get_current_user_point(token_data=token)


@point_router.get("/today-point")
async def get_today_point(
    token: Annotated[TokenData, Depends(get_current_user)],
    point_controller: PointController = Depends(),
):
    return await point_controller.get_today_point(token_data=token)


@point_router.get("/weekly-point")
async def get_weekly_point(
    token: Annotated[TokenData, Depends(get_current_user)],
    point_controller: PointController = Depends(),
):
    return await point_controller.get_weekly_point(token_data=token)


@point_router.get("/monthly-point")
async def get_monthly_point(
    token: Annotated[TokenData, Depends(get_current_user)],
    point_controller: PointController = Depends(),
):
    return await point_controller.get_monthly_point(token_data=token)


@point_router.get("/all-user-point")
async def get_all_user_point(
    token: Annotated[TokenData, Depends(get_current_user)],
    point_controller: PointController = Depends(),
):
    return await point_controller.get_all_user_point(token_data=token)


@point_router.post("/all-user-point-timeseries")
async def get_all_user_point_timeseries(
    token: Annotated[TokenData, Depends(get_current_user)],
    point_controller: PointController = Depends(),
    start_date: str = None,
    end_date: str = None,
):
    return await point_controller.get_all_user_point_timeseries(
        token_data=token, start_date=start_date, end_date=end_date
    )

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

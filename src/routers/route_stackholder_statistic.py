import datetime
from typing_extensions import Annotated
from fastapi import Depends, HTTPException, Query
from fastapi import APIRouter

from config.schemas.common_schema import StandardResponse, TokenData
from config.schemas.sampah_schema import Timeseries
from src.controllers.statistic.controller_statistics import StatisticController
from src.controllers.service_common import get_current_user


statistic_stackholder_router = APIRouter(
    prefix="/api/v1/stackholder", tags=["Statistics_Stackholder"]
)


@statistic_stackholder_router.get("/total_data_statistic")
async def statistic_get_total_data(
    token: Annotated[TokenData, Depends(get_current_user)],
    statistic_controller: StatisticController = Depends(),
):
    return await statistic_controller.get_total_statistic(token)


@statistic_stackholder_router.get("/data_statistic")
async def statistic_get_data(
    token: Annotated[TokenData, Depends(get_current_user)],
    data_type: str = Query("all"),  # Data type (default all)
    status: str = Query("all"),  # Status (default all)
    page: int = Query(1, ge=1),  # Page number (default 1)
    page_size: int = Query(10, ge=1, le=100),  # Page size (default 10, max 100)
    statistic_controller: StatisticController = Depends(),
):
    return await statistic_controller.get_data_statistic(
        token, data_type, status, page, page_size
    )


@statistic_stackholder_router.get("/data_statistic_timeseries")
async def statistic_get_data_timeseries(
    token: Annotated[TokenData, Depends(get_current_user)],
    data_type: str = Query("all"),  # Data type (default all)
    status: str = Query("all"),  # Status (default all)
    start_date: datetime.datetime = Query(),
    end_date: datetime.datetime = Query(),
    page: int = Query(1, ge=1),  # Page number (default 1)
    page_size: int = Query(10, ge=1, le=100),  # Page size (default 10, max 100)
    statistic_controller: StatisticController = Depends(),
):
    return await statistic_controller.get_data_statistic_timeseries(
        token, data_type, status, start_date, end_date, page, page_size
    )

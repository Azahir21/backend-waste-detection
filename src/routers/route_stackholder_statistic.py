import datetime
from typing import Optional
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
    token: TokenData = Depends(get_current_user),
    data_type: str = Query(
        "all",
        description="Data type (default all). Options: garbage_pile, garbage_pcs, and all",
    ),
    status: str = Query(
        "all",
        description="Status (default all). Options: all, collected, not_collected",
    ),
    start_date: Optional[datetime.datetime] = Query(
        None, description="Start date for capture time filter"
    ),
    end_date: Optional[datetime.datetime] = Query(
        None, description="End date for capture time filter"
    ),
    sort_by: str = Query(
        "id",
        description=(
            "Field to sort by. Options: id, is_waste_pile, address, pickup_status, "
            "capture_time, waste_count, pickup_by_user, pickup_at"
        ),
    ),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    search: str = Query("", description="Search query (empty means no search)"),
    page: int = Query(1, ge=1, description="Page number (default 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Page size (default 10, max 100)"
    ),
    statistic_controller: StatisticController = Depends(),
):
    return await statistic_controller.get_data_statistic(
        token,
        data_type,
        status,
        start_date,
        end_date,
        sort_by,
        sort_order,
        search,
        page,
        page_size,
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

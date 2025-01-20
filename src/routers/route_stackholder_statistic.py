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


@statistic_stackholder_router.get("/get_collected_data_statistic")
async def statistic_get_data_collected(
    token: Annotated[TokenData, Depends(get_current_user)],
    data_type: str = Query("all"),  # Data type (default all)
    page: int = Query(1, ge=1),  # Page number (default 1)
    page_size: int = Query(10, ge=1, le=100),  # Page size (default 10, max 100)
    statistic_controller: StatisticController = Depends(),
):
    return await statistic_controller.get_collection_statistic(
        token, data_type, page, page_size
    )


@statistic_stackholder_router.get("/get_collected_data_statistic_timeseries")
async def statistic_get_data_collected_timeseries(
    token: Annotated[TokenData, Depends(get_current_user)],
    data_type: str = Query("all"),  # Data type (default all)
    start_date: datetime.datetime = Query(),
    end_date: datetime.datetime = Query(),
    page: int = Query(1, ge=1),  # Page number (default 1)
    page_size: int = Query(10, ge=1, le=100),  # Page size (default 10, max 100)
    statistic_controller: StatisticController = Depends(),
):
    return await statistic_controller.get_collection_statistic_timeseries(
        token, data_type, start_date, end_date, page, page_size
    )


@statistic_stackholder_router.get("/get_uncollected_data_statistic")
async def statistic_get_data_uncollected(
    token: Annotated[TokenData, Depends(get_current_user)],
    data_type: str = Query("all"),  # Data type (default all)
    page: int = Query(1, ge=1),  # Page number (default 1)
    page_size: int = Query(10, ge=1, le=100),  # Page size (default 10, max 100)
    statistic_controller: StatisticController = Depends(),
):
    return await statistic_controller.get_uncollected_statistic(
        token, data_type, page, page_size
    )


@statistic_stackholder_router.get("/get_uncollected_data_statistic_timeseries")
async def statistic_get_data_uncollected_timeseries(
    token: Annotated[TokenData, Depends(get_current_user)],
    data_type: str = Query("all"),  # Data type (default all)
    start_date: datetime.datetime = Query(),
    end_date: datetime.datetime = Query(),
    page: int = Query(1, ge=1),  # Page number (default 1)
    page_size: int = Query(10, ge=1, le=100),  # Page size (default 10, max 100)
    statistic_controller: StatisticController = Depends(),
):
    return await statistic_controller.get_uncollected_statistic_timeseries(
        token, data_type, start_date, end_date, page, page_size
    )


##################################
# @statistic_stackholder_router.get("/get_sampah_detail/{sampah_id}")
# async def statistic_get_sampah_detail(
#     sampah_id: int,
#     token: Annotated[TokenData, Depends(get_current_user)],
#     statistic_controller: StatisticController = Depends(),
# ):
#     return await statistic_controller.get_sampah_detail(token, sampah_id)


# @statistic_stackholder_router.get("/get_all_statistic")
# async def statistic_get_all(
#     token: Annotated[TokenData, Depends(get_current_user)],
#     # page: int = Query(1, ge=1),  # Page number (default 1)
#     # page_size: int = Query(10, ge=1, le=100),  # Page size (default 10, max 100)
#     statistic_controller: StatisticController = Depends(),
# ):
#     return await statistic_controller.get_all_statistic(token)


# @statistic_stackholder_router.post("/get_all_statistic_timeseries")
# async def statistic_get_timeseries(
#     token: Annotated[TokenData, Depends(get_current_user)],
#     time_series: Timeseries,
#     page: int = Query(1, ge=1),  # Page number (default 1)
#     page_size: int = Query(10, ge=1, le=100),  # Page size (default 10, max 100)
#     statistic_controller: StatisticController = Depends(),
# ):
#     return await statistic_controller.get_all_statistic_timeseries(
#         token, time_series.start_date, time_series.end_date
#     )


# @statistic_stackholder_router.get("/get_garbage_pile_statistic")
# async def statistic_get_garbage_pile(
#     token: Annotated[TokenData, Depends(get_current_user)],
#     statistic_controller: StatisticController = Depends(),
# ):
#     return await statistic_controller.get_garbage_pile_statistic(token)


# @statistic_stackholder_router.post("/get_garbage_pile_statistic_timeseries")
# async def statistic_get_garbage_pile_timeseries(
#     token: Annotated[TokenData, Depends(get_current_user)],
#     time_series: Timeseries,
#     statistic_controller: StatisticController = Depends(),
# ):
#     return await statistic_controller.get_garbage_pile_statistic_timeseries(
#         token, time_series.start_date, time_series.end_date
#     )


# @statistic_stackholder_router.get("/get_garbage_pcs_statistic")
# async def statistic_get_garbage_pcs(
#     token: Annotated[TokenData, Depends(get_current_user)],
#     statistic_controller: StatisticController = Depends(),
# ):
#     return await statistic_controller.get_garbage_pcs_statistic(token)


# @statistic_stackholder_router.post("/get_garbage_pcs_statistic_timeseries")
# async def statistic_get_garbage_pcs_timeseries(
#     token: Annotated[TokenData, Depends(get_current_user)],
#     time_series: Timeseries,
#     statistic_controller: StatisticController = Depends(),
# ):
#     return await statistic_controller.get_garbage_pcs_statistic_timeseries(
#         token, time_series.start_date, time_series.end_date
#     )

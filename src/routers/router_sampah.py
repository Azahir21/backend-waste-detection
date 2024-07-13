from typing_extensions import Annotated
from fastapi import APIRouter, Depends
from config.schemas.common_schema import TokenData
from config.schemas.sampah_schema import Timeseries
from src.controllers.sampah.controller_sampah import SampahController
from src.controllers.service_common import get_current_user


sampah_router = APIRouter(prefix="/api/v1", tags=["Sampah"])


@sampah_router.get("/sampah")
async def get_all_user_sampah(
    token: Annotated[TokenData, Depends(get_current_user)],
    sampah_controller: SampahController = Depends(),
):
    return await sampah_controller.get_all_sampah(token)


@sampah_router.post("/sampah/timeseries")
async def get_sampah_timeseries(
    token: Annotated[TokenData, Depends(get_current_user)],
    time_series: Timeseries,
    sampah_controller: SampahController = Depends(),
):
    return await sampah_controller.get_sampah_timeseries(
        token, time_series.start_date, time_series.end_date
    )

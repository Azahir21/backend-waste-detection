from typing_extensions import Annotated
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    UploadFile,
)
from config.schemas.common_schema import StandardResponse, TokenData
from config.schemas.sampah_schema import InputSampah, Timeseries
from src.controllers.sampah.controller_sampah import SampahController
from src.controllers.service_common import get_current_user


sampah_user_router = APIRouter(prefix="/api/v1/user", tags=["Sampah User"])


@sampah_user_router.get("/sampah")
async def get_sampah(
    token: Annotated[TokenData, Depends(get_current_user)],
    sampah_controller: SampahController = Depends(),
):
    return await sampah_controller.get_all_user_sampah(token)


@sampah_user_router.get("/sampah/{sampah_id}")
async def get_sampah_detail(
    token: Annotated[TokenData, Depends(get_current_user)],
    sampah_id: int,
    sampah_controller: SampahController = Depends(),
):
    return await sampah_controller.get_sampah_detail(token, sampah_id)


@sampah_user_router.post("/sampah/images")
async def store_image(
    token: Annotated[TokenData, Depends(get_current_user)],
    file: UploadFile = File(...),
    sampah_controller: SampahController = Depends(),
):
    return await sampah_controller.store_image(file)


@sampah_user_router.post("/sampah")
async def post_sampah(
    input_sampah: InputSampah,
    token: TokenData = Depends(get_current_user),
    sampah_controller: SampahController = Depends(),
):
    return await sampah_controller.post_sampah(input_sampah, token)
    # return StandardResponse(detail="Success Post Sampah")


@sampah_user_router.post("/sampah/timeseries")
async def get_sampah_timeseries(
    token: Annotated[TokenData, Depends(get_current_user)],
    time_series: Timeseries,
    sampah_controller: SampahController = Depends(),
):
    return await sampah_controller.get_sampah_timeseries(
        token, time_series.start_date, time_series.end_date
    )

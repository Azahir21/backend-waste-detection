import datetime
from typing_extensions import Annotated
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Query,
    UploadFile,
)
from config.schemas.common_schema import TokenData
from config.schemas.sampah_schema import InputSampah, Timeseries
from src.controllers.sampah.controller_sampah import SampahController
from src.controllers.service_common import get_current_user


sampah_user_router = APIRouter(prefix="/api/v1/user", tags=["Sampah User"])


@sampah_user_router.get("/sampah")
async def get_sampah(
    token: Annotated[TokenData, Depends(get_current_user)],
    page: int = Query(1, ge=1),  # Page number (default 1)
    page_size: int = Query(10, ge=1, le=100),  # Page size (default 10, max 100)
    sampah_controller: SampahController = Depends(),
):
    return await sampah_controller.get_all_user_sampah(token, page, page_size)


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


@sampah_user_router.post("/sampah/timeseries")
async def get_sampah_timeseries(
    token: Annotated[TokenData, Depends(get_current_user)],
    time_series: Timeseries,
    sampah_controller: SampahController = Depends(),
):
    return await sampah_controller.get_sampah_timeseries(
        token, time_series.start_date, time_series.end_date
    )


@sampah_user_router.post("/sampah-v2")
async def post_sampah_v2(
    lang: str = Query("id"),
    longitude: float = Query(...),
    latitude: float = Query(...),
    address: str = Query(...),
    use_garbage_pile_model: bool = Query(False),
    capture_date: datetime.datetime = Query(...),
    file: UploadFile = File(...),
    token: TokenData = Depends(get_current_user),
    sampah_controller: SampahController = Depends(),
):
    return await sampah_controller.post_sampah_v2(
        token,
        lang,
        longitude,
        latitude,
        address,
        use_garbage_pile_model,
        capture_date,
        file,
    )

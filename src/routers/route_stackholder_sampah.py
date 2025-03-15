from fastapi import APIRouter, Body, HTTPException, Path
from fastapi import Depends, Query
from datetime import datetime
from typing_extensions import Annotated
from config.schemas.common_schema import TokenData
from src.controllers.sampah.controller_sampah import SampahController
from src.controllers.service_common import get_current_user


sampah_stackholder_router = APIRouter(
    prefix="/api/v1/stackholder", tags=["Sampah Stackholder"]
)


@sampah_stackholder_router.get("/sampah")
async def get_all_user_sampah(
    token: Annotated[TokenData, Depends(get_current_user)],
    data_type: str = Query("all"),
    status: str = Query("all"),
    sampah_controller: SampahController = Depends(),
):
    return await sampah_controller.get_all_sampah(token, data_type, status)


@sampah_stackholder_router.get("/sampah/timeseries")
async def get_sampah_timeseries(
    token: Annotated[TokenData, Depends(get_current_user)],
    data_type: str = Query("all"),
    status: str = Query("all"),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    sampah_controller: SampahController = Depends(),
):
    return await sampah_controller.get_sampah_timeseries(
        token, data_type, status, start_date, end_date
    )


@sampah_stackholder_router.put("/sampah/pickup/{sampah_id}")
async def pickup_garbage(
    token: Annotated[TokenData, Depends(get_current_user)],
    sampah_id: int = Path(...),
    image_base64: str = Body(...),
    sampah_controller: SampahController = Depends(),
):
    if token.role != "stackholder" and token.role != "admin":
        raise HTTPException(status_code=400, detail="Not Permitted")
    return await sampah_controller.pickup_garbage(token, sampah_id, image_base64)


@sampah_stackholder_router.put("/sampah/unpickup/{sampah_id}")
async def unpickup_garbage(
    token: Annotated[TokenData, Depends(get_current_user)],
    sampah_id: int = Path(...),
    sampah_controller: SampahController = Depends(),
):
    if token.role != "admin":
        raise HTTPException(status_code=400, detail="Not Permitted")
    return await sampah_controller.unpickup_garbage(token, sampah_id)

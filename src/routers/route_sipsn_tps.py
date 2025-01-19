from fastapi import APIRouter
from config.schemas.sipsn_schema import TPS3RRequest
from src.controllers.service_sipsn import fetch_tps3r_data


sipsn_tps_router = APIRouter(prefix="/api/v1/stackholder", tags=["SIPSN TPS"])


@sipsn_tps_router.post("/tps")
async def get_tps3r_data(request_data: TPS3RRequest):
    result = await fetch_tps3r_data(request_data)
    return result

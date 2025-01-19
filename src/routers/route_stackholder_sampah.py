from fastapi import APIRouter


sampah_stackholder_router = APIRouter(
    prefix="/api/v1/stackholder", tags=["Sampah Stackholder"]
)


@sampah_stackholder_router.get("/sampah")
async def get_all_sampah():
    return {"message": "This is sampah stackholder router"}

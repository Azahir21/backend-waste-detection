import base64
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from geopy.distance import geodesic
from geoalchemy2.shape import to_shape
from config.schemas.common_schema import TokenData
from config.schemas.sampah_schema import InputSampah
from src.controllers.service_common import (
    insert_image_to_local,
    save_image_base64_to_local,
)
from src.repositories.repository_user import UserRepository
from src.repositories.repository_sampah import SampahRepository


class SampahController:
    def __init__(
        self,
        sampah_repository: SampahRepository = Depends(),
        user_repository: UserRepository = Depends(),
    ):
        self.sampah_repository = sampah_repository
        self.user_repository = user_repository

    async def get_all_user_sampah(self, token: TokenData, page: int, page_size: int):
        user = await self.user_repository.find_user_by_username(token.name)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        all_data, total_count = await self.sampah_repository.get_all_user_sampah(
            user.id, page, page_size
        )
        return {
            "data": all_data,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
        }

    async def get_sampah_detail(self, token: TokenData, sampah_id: int):
        data = await self.sampah_repository.get_sampah_detail(sampah_id)
        if data is None:
            raise HTTPException(status_code=404, detail="Sampah not found")
        data.image = f"https://jjmbm5rz-8000.asse.devtunnels.ms/garbage-image/{data.image.split('/')[-1]}"
        return data

    async def get_all_sampah(self, token: TokenData, data_type: str, status: str):
        data = await self.sampah_repository.get_all_sampah(data_type, status)
        for item in data:
            item.image = f"https://jjmbm5rz-8000.asse.devtunnels.ms/garbage-image/{item.image.split('/')[-1]}"
        return data

    async def store_image(self, file):
        filename = insert_image_to_local(file, folder="garbage_image")
        filename = f"assets/garbage_image/{filename}"
        return {"image_path": filename}

    async def post_sampah(self, input_sampah: InputSampah, token: TokenData):
        user = await self.user_repository.find_user_by_username(token.name)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        current_time = input_sampah.capture_date
        time_threshold = current_time - timedelta(minutes=15)

        previous_uploads = await self.sampah_repository.find_uploads_within_timeframe(
            user.id, time_threshold
        )

        # chack if there is any upload within 15 meters and 15 minutes
        for upload in previous_uploads:
            geom_wkt = to_shape(upload.geom).wkt
            longitude, latitude = (
                geom_wkt.replace("POINT (", "").replace(")", "").split()
            )
            upload_location = (latitude, longitude)
            current_location = (input_sampah.latitude, input_sampah.longitude)
            distance = geodesic(upload_location, current_location).meters
            if distance <= 15:
                raise HTTPException(
                    status_code=400,
                    detail="Upload within 15 meters and 15 minutes detected",
                )
        input_sampah.image = save_image_base64_to_local(
            input_sampah.image, input_sampah.filename, folder="garbage_image"
        )
        return await self.sampah_repository.insert_new_sampah(input_sampah, user.id)

    async def get_sampah_timeseries(
        self,
        token: TokenData,
        data_type: str,
        status: str,
        start_date: datetime,
        end_date: datetime,
    ):
        data = await self.sampah_repository.get_sampah_timeseries(
            data_type, status, start_date, end_date
        )
        for item in data:
            item.image = f"https://jjmbm5rz-8000.asse.devtunnels.ms/garbage-image/{item.image.split('/')[-1]}"
        return data

    async def pickup_garbage(self, token: TokenData, sampah_id: int):
        return await self.sampah_repository.pickup_garbage(token, sampah_id)

    async def unpickup_garbage(self, token: TokenData, sampah_id: int):
        return await self.sampah_repository.unpickup_garbage(token, sampah_id)

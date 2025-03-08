import base64
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, UploadFile
from geopy.distance import geodesic
from geoalchemy2.shape import to_shape
from config.schemas.common_schema import TokenData
from config.schemas.sampah_schema import InputSampah
from src.controllers.sampah.service_predict import process_image
from src.controllers.service_common import insert_image_to_local
from src.repositories.repository_user import UserRepository
from src.repositories.repository_sampah import SampahRepository
import os
import requests


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
        input_sampah.image_url = await self.download_image(input_sampah.image_url)
        return await self.sampah_repository.insert_new_sampah(input_sampah, user.id)

    async def download_image(self, image_url: str):
        response = requests.get(image_url)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, detail="Failed to download image"
            )
        image_data = response.content
        filename = os.path.basename(image_url)
        file_path = os.path.join("assets", "garbage_image", filename)
        with open(file_path, "wb") as f:
            f.write(image_data)
        file_path = f"assets/garbage_image/{filename}"
        return file_path

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

    async def post_sampah_v2(
        self,
        token: TokenData,
        lang: str,
        longitude: float,
        latitude: float,
        address: str,
        use_garbage_pile_model: bool,
        capture_date: datetime,
        file: UploadFile,
    ):
        user = await self.user_repository.find_user_by_username(token.name)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        same_capture = await self.sampah_repository.find_same_capture_time(
            user.id, capture_date
        )
        if same_capture:
            raise HTTPException(
                status_code=400,
                detail="Image with the same capture time already exists",
            )

        current_time = capture_date
        time_threshold = current_time - timedelta(minutes=15)

        previous_uploads = await self.sampah_repository.find_uploads_within_timeframe(
            user.id, time_threshold
        )

        # chack if there is any upload within 15 meters and 15 minutes
        for upload in previous_uploads:
            geom_wkt = to_shape(upload.geom).wkt
            previous_longitude, previous_latitude = (
                geom_wkt.replace("POINT (", "").replace(")", "").split()
            )
            upload_location = (previous_latitude, previous_longitude)
            current_location = (latitude, longitude)
            distance = geodesic(upload_location, current_location).meters
            if distance <= 15:
                raise HTTPException(
                    status_code=400,
                    detail="Upload within 15 meters and 15 minutes detected",
                )
        file.filename = f"{token.name}_{file.filename}"
        filename = insert_image_to_local(file, folder="original_image")
        processed_imagepath, total_point, list_sampah_items = process_image(
            filename, use_garbage_pile_model
        )

        input_sampah = InputSampah(
            longitude=longitude,
            latitude=latitude,
            address=address,
            capture_date=capture_date,
            image_url=f"assets/detected_image/{processed_imagepath}",
            point=total_point,
            is_waste_pile=use_garbage_pile_model,
            sampah_items=list_sampah_items,
        )
        result = await self.sampah_repository.insert_new_sampah(input_sampah, user.id)

        # Define messages in both languages
        messages = {
            "id": {
                "high": f"Selamat! Anda mendapat {total_point} poin!",
                "medium": f"Bagus! Anda mendapat {total_point} poin. Terus tingkatkan kontribusi Anda!",
                "low": f"Terima kasih atas kontribusi Anda! Anda mendapat {total_point} poin.",
            },
            "en": {
                "high": f"Congratulations! You earned {total_point} points!",
                "medium": f"Good! You earned {total_point} points. Keep increasing your contribution!",
                "low": f"Thank you for your contribution! You earned {total_point} points.",
            },
            "jp": {
                "high": f"おめでとうございます！{total_point}ポイントを獲得しました！",
                "medium": f"良い！{total_point}ポイントを獲得しました。貢献度を上げ続けましょう！",
                "low": f"ご協力ありがとうございます！{total_point}ポイントを獲得しました。",
            },
        }

        # Default to Indonesian, but could be made configurable
        lang = lang if lang in messages else "id"

        message = ""
        if total_point >= 100:
            message = messages[lang]["high"]
        elif total_point >= 50:
            message = messages[lang]["medium"]
        else:
            message = messages[lang]["low"]

        return {
            "message": message,
            "badge": result["badge"],
            "updated_badge": result["updated_badge"],
        }

import asyncio
import base64
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, UploadFile
from geopy.distance import geodesic
from geoalchemy2.shape import to_shape
from config.schemas.common_schema import TokenData
from config.schemas.sampah_schema import InputSampah
from src.controllers.sampah.service_predict import process_image
from src.controllers.service_common import (
    insert_image_to_local,
    insert_image_to_local_base64,
)
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
        if "detected_image" in data.image:
            data.image = f"https://jjmbm5rz-8000.asse.devtunnels.ms/detected-image/{data.image.split('/')[-1]}"
        else:
            data.image = f"https://jjmbm5rz-8000.asse.devtunnels.ms/garbage-image/{data.image.split('/')[-1]}"
        if data.evidence:
            data.evidence = f"https://jjmbm5rz-8000.asse.devtunnels.ms/evidence-image/{data.evidence.split('/')[-1]}"
        return data

    async def get_all_sampah(self, token: TokenData, data_type: str, status: str):
        data = await self.sampah_repository.get_all_sampah(data_type, status)
        for item in data:
            if item.evidence:
                item.evidence = f"https://jjmbm5rz-8000.asse.devtunnels.ms/pickup-image/{item.evidence.split('/')[-1]}"

            if "detected_image" in item.image:
                item.image = f"https://jjmbm5rz-8000.asse.devtunnels.ms/detected-image/{item.image.split('/')[-1]}"
            else:
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
            if item.evidence:
                item.evidence = f"https://jjmbm5rz-8000.asse.devtunnels.ms/evidence-image/{item.evidence.split('/')[-1]}"
            if "detected_image" in item.image:
                item.image = f"https://jjmbm5rz-8000.asse.devtunnels.ms/detected-image/{item.image.split('/')[-1]}"
            else:
                item.image = f"https://jjmbm5rz-8000.asse.devtunnels.ms/garbage-image/{item.image.split('/')[-1]}"
        return data

    async def pickup_garbage(self, token: TokenData, sampah_id: int, image_base64: str):
        # save image to local and get the path
        image_path = insert_image_to_local_base64(
            image_base64, f"{sampah_id}_pickup_evidence", folder="pickup_image"
        )
        return await self.sampah_repository.pickup_garbage(token, sampah_id, image_path)

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
        # Validate user
        user = await self.user_repository.find_user_by_username(token.name)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        # Define time thresholds
        time_threshold = capture_date - timedelta(minutes=15)

        # Run the two independent database queries concurrently:
        same_capture, previous_uploads = await asyncio.gather(
            self.sampah_repository.find_same_capture_time(user.id, capture_date),
            self.sampah_repository.find_uploads_within_timeframe(
                user.id, time_threshold
            ),
        )

        if same_capture:
            raise HTTPException(
                status_code=400,
                detail="Image with the same capture time already exists",
            )

        # Check if any previous upload is within 15 meters and 15 minutes

        for upload in previous_uploads:
            # Convert the WKT string to extract coordinates
            geom = to_shape(upload.geom).wkt
            previous_longitude, previous_latitude = geom.x, geom.y
            upload_location = (previous_latitude, previous_longitude)
            current_location = (latitude, longitude)
            distance = geodesic(upload_location, current_location).meters
            if distance <= 15:
                raise HTTPException(
                    status_code=400,
                    detail="Upload within 15 meters and 15 minutes detected",
                )

        # Rename and store the file
        file.filename = f"{token.name}_{file.filename}"
        filename = insert_image_to_local(file, folder="original_image")

        # Offload the CPU-bound image processing to a separate thread
        processed_imagepath, total_point, list_sampah_items = await asyncio.to_thread(
            process_image, filename, use_garbage_pile_model
        )

        # Prepare the input for new sampah entry
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

        # Insert the new sampah record (await the async DB operation)
        result = await self.sampah_repository.insert_new_sampah(input_sampah, user.id)

        messages = {
            "id": {
                "high": {
                    "title": "Wow, Kontribusi Luar Biasa! 🌟",
                    "message": f"Anda mendapat {total_point} poin dari laporan ini.",
                },
                "medium": {
                    "title": "Hebat, Terus Maju! 👏",
                    "message": f"Anda mendapat {total_point} poin. Terus berkontribusi!",
                },
                "low": {
                    "title": "Langkah Awal yang Baik! 👍",
                    "message": f"Anda mendapat {total_point} poin dari kontribusi Anda.",
                },
            },
            "en": {
                "high": {
                    "title": "Amazing Work, Champion! 🌟",
                    "message": f"You earned {total_point} points from this report.",
                },
                "medium": {
                    "title": "Great Progress, Keep Going! 👏",
                    "message": f"You earned {total_point} points. Keep contributing!",
                },
                "low": {
                    "title": "Every Bit Counts, Thanks! 👍",
                    "message": f"You earned {total_point} points from your contribution.",
                },
            },
            "jp": {
                "high": {
                    "title": "素晴らしい成果です！🌟",
                    "message": f"このレポートから{total_point}ポイントを獲得しました。",
                },
                "medium": {
                    "title": "素敵な貢献、続けましょう！👏",
                    "message": f"{total_point}ポイントを獲得。貢献を続けましょう！",
                },
                "low": {
                    "title": "一歩前進、ありがとう！👍",
                    "message": f"あなたの貢献から{total_point}ポイントを獲得しました。",
                },
            },
        }
        lang = lang if lang in messages else "id"

        if total_point >= 100:
            message = messages[lang]["high"]
        elif total_point >= 50:
            message = messages[lang]["medium"]
        else:
            message = messages[lang]["low"]

        return {
            "title": message["title"],
            "message": message["message"],
            "badge": result["badge"],
            "updated_badge": result["updated_badge"],
            "report-id": result["id"],
        }

from datetime import datetime
import os
from typing import List
from fastapi import Depends, HTTPException
from config.database import get_db
from config.models import sampah_item_model, sampah_model, jenis_sampah_model
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from geoalchemy2.shape import to_shape
from config.models.badge_model import Badge
from config.models.point_model import Point
from config.schemas.common_schema import TokenData
from config.schemas.sampah_schema import (
    CountObject,
    InputSampah,
    OutputSampah,
    OutputSampahDetail,
    OutputSampahItem,
)
from src.repositories.repository_point import PointRepository


class SampahRepository:
    def __init__(
        self,
        db: Session = Depends(get_db),
        point_repository: PointRepository = Depends(),
    ):
        self.db = db
        self.point_repository = point_repository

    DATABASE_ERROR_MESSAGE = "Database error"

    async def insert_new_sampah(self, input_sampah: InputSampah, user_id):
        try:
            current_time = datetime.now()

            # Insert sampah data
            new_sampah = sampah_model.Sampah(
                userId=user_id,
                address=input_sampah.address,
                imagePath=input_sampah.image_url,
                geom=f"POINT({input_sampah.longitude} {input_sampah.latitude})",
                captureTime=input_sampah.capture_date,
                point=input_sampah.point,
                isGarbagePile=input_sampah.is_waste_pile,
                isPickup=False,
                createdAt=current_time,
                updatedAt=current_time,
            )
            self.db.add(new_sampah)
            self.db.flush()  # Ensure new_sampah.id is available

            # Insert sampah items
            for sampah_item in input_sampah.sampah_items:
                new_sampah_item = sampah_item_model.SampahItem(
                    sampahId=new_sampah.id,
                    jenisSampahId=sampah_item.jenisSampahId,
                    createdAt=datetime.now(),
                    updatedAt=datetime.now(),
                )
                self.db.add(new_sampah_item)

            # Commit the transaction after all items are added
            self.db.commit()
            self.db.refresh(new_sampah)

            # Update user point
            updated_point = await self.point_repository.update_user_point(
                user_id, input_sampah.point
            )

            # Query only the badge that meets the user's point criteria (optimized query)
            user_point = self.db.query(Point).filter(Point.userId == user_id).first()
            if user_point:
                new_badge = (
                    self.db.query(Badge)
                    .filter(Badge.pointMinimum <= user_point.point)
                    .order_by(Badge.pointMinimum.desc())
                    .first()
                )
                # Update user's badge if needed
                if new_badge and (
                    user_point.badgeId is None or new_badge.id > user_point.badgeId
                ):
                    user_point.badgeId = new_badge.id
                    self.db.commit()
                    self.db.refresh(user_point)
                    return {
                        "id": new_sampah.id,
                        "detail": "Success Post Sampah",
                        "badge": new_badge.name,
                        "updated_badge": True,
                    }

            return {
                "id": new_sampah.id,
                "detail": "Success Post Sampah",
                "badge": None,
                "updated_badge": False,
            }

        except SQLAlchemyError as e:
            self.db.rollback()
            if os.path.exists(input_sampah.image_path):
                os.remove(input_sampah.image_path)
            raise HTTPException(
                status_code=500, detail=f"{self.DATABASE_ERROR_MESSAGE}: {str(e)}"
            )

    async def get_all_user_sampah(self, user_id, page, page_size):
        try:
            query = self.db.query(sampah_model.Sampah).filter(
                sampah_model.Sampah.userId == user_id
            )
            total_count = query.count()
            data = (
                query.order_by(sampah_model.Sampah.captureTime.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            return [
                OutputSampah.from_orm(sampah).dict() for sampah in data
            ], total_count
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_all_sampah(self, data_type: str, status: str):
        try:
            query = self.db.query(sampah_model.Sampah).options(
                joinedload(sampah_model.Sampah.sampah_items).joinedload(
                    sampah_item_model.SampahItem.jenis_sampah
                )
            )

            if data_type == "garbage_pile":
                query = query.filter(sampah_model.Sampah.isGarbagePile == True)
            elif data_type == "garbage_pcs":
                query = query.filter(sampah_model.Sampah.isGarbagePile == False)

            if status == "pickup_true":
                query = query.filter(sampah_model.Sampah.isPickup == True)
            elif status == "pickup_false":
                query = query.filter(sampah_model.Sampah.isPickup == False)

            sampahs = query.all()

            if not sampahs:
                raise HTTPException(status_code=404, detail="Sampah not found")

            data = []
            for sampah in sampahs:
                sampah_items_list = [
                    OutputSampahItem(
                        nama=item.jenis_sampah.nama, point=item.jenis_sampah.point
                    )
                    for item in sampah.sampah_items
                ]

                count_objects = self.calculate_objects(sampah_items_list)

                if sampah_items_list and count_objects:
                    data.append(
                        OutputSampahDetail(
                            id=sampah.id,
                            is_waste_pile=sampah.isGarbagePile,
                            address=sampah.address,
                            geom=to_shape(sampah.geom).wkt,
                            captureTime=sampah.captureTime,
                            pickupAt=sampah.pickupAt,
                            is_pickup=sampah.isPickup,
                            pickup_by_user=sampah.pickupByUser,
                            point=sampah.point,
                            total_sampah=len(sampah_items_list),
                            sampah_items=sampah_items_list,
                            count_items=count_objects,
                            image=sampah.imagePath,
                        )
                    )
            return data
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_sampah_detail(self, sampah_id: int):
        try:
            # Fetch the Sampah object with related SampahItems and JenisSampah
            sampah = (
                self.db.query(sampah_model.Sampah)
                .filter(sampah_model.Sampah.id == sampah_id)
                .options(
                    joinedload(sampah_model.Sampah.sampah_items).joinedload(
                        sampah_item_model.SampahItem.jenis_sampah
                    )
                )
                .first()
            )
            if sampah is None:
                raise HTTPException(status_code=404, detail="Sampah not found")

            sampah_items_list = [
                OutputSampahItem(
                    nama=item.jenis_sampah.nama, point=item.jenis_sampah.point
                )
                for item in sampah.sampah_items
            ]

            count_objects = self.calculate_objects(sampah_items_list)

            return OutputSampahDetail(
                id=sampah.id,
                is_waste_pile=sampah.isGarbagePile,
                address=sampah.address,
                geom=to_shape(sampah.geom).wkt,
                captureTime=sampah.captureTime,
                pickupAt=sampah.pickupAt,
                is_pickup=sampah.isPickup,
                pickup_by_user=sampah.pickupByUser,
                point=sampah.point,
                total_sampah=len(sampah_items_list),
                sampah_items=sampah_items_list,
                count_items=count_objects,
                image=sampah.imagePath,
            )
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def find_same_capture_time(self, user_id, capture_time):
        try:
            return (
                self.db.query(sampah_model.Sampah)
                .filter(sampah_model.Sampah.userId == user_id)
                .filter(sampah_model.Sampah.captureTime == capture_time)
                .all()
            )
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def find_uploads_within_timeframe(self, user_id, time_threshold):
        try:
            return (
                self.db.query(sampah_model.Sampah)
                .filter(sampah_model.Sampah.userId == user_id)
                .filter(sampah_model.Sampah.captureTime >= time_threshold)
                .all()
            )
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_sampah_timeseries(self, data_type, status, start_date, end_date):
        try:
            query = (
                self.db.query(sampah_model.Sampah)
                .filter(sampah_model.Sampah.captureTime >= start_date)
                .filter(sampah_model.Sampah.captureTime <= end_date)
                .options(
                    joinedload(sampah_model.Sampah.sampah_items).joinedload(
                        sampah_item_model.SampahItem.jenis_sampah
                    )
                )
            )

            if data_type == "garbage_pile":
                query = query.filter(sampah_model.Sampah.isGarbagePile == True)
            elif data_type == "garbage_pcs":
                query = query.filter(sampah_model.Sampah.isGarbagePile == False)

            if status == "pickup_true":
                query = query.filter(sampah_model.Sampah.isPickup == True)
            elif status == "pickup_false":
                query = query.filter(sampah_model.Sampah.isPickup == False)

            sampahs = query.all()

            if not sampahs:
                raise HTTPException(status_code=404, detail="Sampah not found")

            data = []
            for sampah in sampahs:
                sampah_items_list = [
                    OutputSampahItem(
                        nama=item.jenis_sampah.nama, point=item.jenis_sampah.point
                    )
                    for item in sampah.sampah_items
                ]
                count_objects = self.calculate_objects(sampah_items_list)

                if sampah_items_list and count_objects:
                    data.append(
                        OutputSampahDetail(
                            id=sampah.id,
                            is_waste_pile=sampah.isGarbagePile,
                            address=sampah.address,
                            geom=to_shape(sampah.geom).wkt,
                            captureTime=sampah.captureTime,
                            pickupAt=sampah.pickupAt,
                            is_pickup=sampah.isPickup,
                            pickup_by_user=sampah.pickupByUser,
                            point=sampah.point,
                            total_sampah=len(sampah_items_list),
                            sampah_items=sampah_items_list,
                            count_items=count_objects,
                            image=sampah.imagePath,
                        )
                    )
            print(len(data))
            return data
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    def calculate_objects(self, detected_objects: List[OutputSampahItem]):
        object_summary = {}
        for obj in detected_objects:
            name = obj.nama
            points = obj.point
            if name in object_summary:
                object_summary[name].count += 1
                object_summary[name].point += points
            else:
                object_summary[name] = CountObject(name=name, count=1, point=points)
        return list(object_summary.values())

    async def pickup_garbage(self, token: TokenData, sampah_id: int):
        try:
            sampah = self.db.query(sampah_model.Sampah).filter(
                sampah_model.Sampah.id == sampah_id
            )
            if not sampah.first():
                raise HTTPException(status_code=404, detail="Sampah not found")
            if sampah.first().isPickup:
                raise HTTPException(status_code=400, detail="Sampah already picked up")
            sampah.update(
                {
                    "isPickup": True,
                    "pickupAt": datetime.now(),
                    "pickupByUser": token.name,
                }
            )
            self.db.commit()
            return {"detail": "Success Update Sampah Status"}
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def unpickup_garbage(self, token: TokenData, sampah_id: int):
        try:
            sampah = self.db.query(sampah_model.Sampah).filter(
                sampah_model.Sampah.id == sampah_id
            )
            if not sampah.first():
                raise HTTPException(status_code=404, detail="Sampah not found")
            if not sampah.first().isPickup:
                raise HTTPException(status_code=400, detail="Sampah already unpicked")
            sampah.update(
                {
                    "isPickup": False,
                    "pickupAt": None,
                    "pickupByUser": None,
                }
            )
            self.db.commit()
            return {"detail": "Success Update Sampah Status"}
        except SQLAlchemyError:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

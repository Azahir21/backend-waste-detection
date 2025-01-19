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
                imagePath=input_sampah.image,
                geom=f"POINT({input_sampah.longitude} {input_sampah.latitude})",
                captureTime=input_sampah.capture_date,
                point=input_sampah.point,
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
                        "detail": "Success Post Sampah",
                        "badge": new_badge.name,
                        "updated_badge": True,
                    }

            return {
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

    async def get_all_user_sampah(self, user_id):
        try:
            data = (
                self.db.query(sampah_model.Sampah)
                .filter(sampah_model.Sampah.userId == user_id)
                .all()
            )
            return [OutputSampah.from_orm(sampah).dict() for sampah in data]
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_all_sampah(self):
        try:
            sampahs = (
                self.db.query(sampah_model.Sampah)
                .options(
                    joinedload(sampah_model.Sampah.sampah_items).joinedload(
                        sampah_item_model.SampahItem.jenis_sampah
                    )
                )
                .all()
            )
            if sampahs is None:
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

                data.append(
                    OutputSampahDetail(
                        id=sampah.id,
                        address=sampah.address,
                        geom=to_shape(sampah.geom).wkt,
                        captureTime=sampah.captureTime,
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
                address=sampah.address,
                geom=to_shape(sampah.geom).wkt,
                image=sampah.imagePath,
                captureTime=sampah.captureTime,
                point=sampah.point,
                total_sampah=len(sampah_items_list),
                sampah_items=sampah_items_list,
                count_items=count_objects,
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

    async def get_sampah_timeseries(self, start_date, end_date):
        try:
            sampahs = (
                self.db.query(sampah_model.Sampah)
                .filter(sampah_model.Sampah.captureTime >= start_date)
                .filter(sampah_model.Sampah.captureTime <= end_date)
                .options(
                    joinedload(sampah_model.Sampah.sampah_items).joinedload(
                        sampah_item_model.SampahItem.jenis_sampah
                    )
                )
                .all()
            )
            if sampahs is None:
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

                data.append(
                    OutputSampahDetail(
                        id=sampah.id,
                        address=sampah.address,
                        geom=to_shape(sampah.geom).wkt,
                        captureTime=sampah.captureTime,
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

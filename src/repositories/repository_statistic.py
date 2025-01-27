from fastapi import Depends, HTTPException
from config.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from geoalchemy2.shape import to_shape

from config.models.sampah_item_model import SampahItem
from config.models.sampah_model import Sampah
from config.models.user_model import User
from config.schemas.sampah_schema import (
    StatisticOutput,
    WasteCollected,
    WasteNotCollected,
)


class StatisticRepository:
    def __init__(
        self,
        db: Session = Depends(get_db),
    ):
        self.db = db

    DATABASE_ERROR_MESSAGE = "Database error"

    async def get_total_statistic(self, token):
        try:
            query_collected_garbage_pile = (
                self.db.query(Sampah)
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(
                    Sampah.isPickup == True,
                    Sampah.isGarbagePile == True,
                    SampahItem.id.isnot(None),
                )
                .count()
            )
            query_collected_garbage_pcs = (
                self.db.query(Sampah)
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(
                    Sampah.isPickup == True,
                    Sampah.isGarbagePile == False,
                    SampahItem.id.isnot(None),
                )
                .count()
            )
            query_not_collected_garbage_pile = (
                self.db.query(Sampah)
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(
                    Sampah.isPickup == False,
                    Sampah.isGarbagePile == True,
                    SampahItem.id.isnot(None),
                )
                .count()
            )
            query_not_collected_garbage_pcs = (
                self.db.query(Sampah)
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(
                    Sampah.isPickup == False,
                    Sampah.isGarbagePile == False,
                    SampahItem.id.isnot(None),
                )
                .count()
            )
            return {
                "collected_garbage_pile": query_collected_garbage_pile,
                "collected_garbage_pcs": query_collected_garbage_pcs,
                "not_collected_garbage_pile": query_not_collected_garbage_pile,
                "not_collected_garbage_pcs": query_not_collected_garbage_pcs,
                "total_collected": query_collected_garbage_pile
                + query_collected_garbage_pcs,
                "total_not_collected": query_not_collected_garbage_pile
                + query_not_collected_garbage_pcs,
            }

        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_data_statistic(
        self, token, data_type: str, status: str, page: int, page_size: int
    ):
        try:
            query = self.db.query(Sampah).filter(
                Sampah.isPickup == (status == "collected")
            )

            if data_type == "garbage_pile":
                query = query.filter(Sampah.isGarbagePile == True)
            elif data_type == "garbage_pcs":
                query = query.filter(Sampah.isGarbagePile == False)

            if status == "collected":
                query = query.filter(Sampah.isPickup == True)
            elif status == "not_collected":
                query = query.filter(Sampah.isPickup == False)

            total_count = query.count()
            sampahs = query.offset((page - 1) * page_size).limit(page_size).all()

            return sampahs, total_count

        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_data_statistic(
        self, token, data_type: str, status: str, page: int, page_size: int
    ):
        try:
            query = self.db.query(
                Sampah.id,
                Sampah.isGarbagePile.label("is_waste_pile"),
                Sampah.address,
                Sampah.geom,
                Sampah.pickupAt.label("pickup_at"),
                Sampah.captureTime.label("capture_time"),
                func.count(SampahItem.id).label("waste_count"),
                Sampah.pickupByUser.label("pickup_by_user"),
            ).join(SampahItem, Sampah.id == SampahItem.sampahId)

            if status == "collected":
                query = query.filter(Sampah.isPickup == True)
            elif status == "uncollected":
                query = query.filter(Sampah.isPickup == False)

            if data_type == "garbage_pile":
                query = query.filter(Sampah.isGarbagePile == True)
            elif data_type == "garbage_pcs":
                query = query.filter(Sampah.isGarbagePile == False)

            result = (
                query.group_by(Sampah.id, Sampah.isGarbagePile, Sampah.pickupByUser)
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )

            result_list = [
                {
                    "id": item.id,
                    "is_waste_pile": item.is_waste_pile,
                    "address": item.address,
                    "geom": to_shape(item.geom).wkt,
                    "pickup_at": item.pickup_at,
                    "capture_time": item.capture_time,
                    "waste_count": item.waste_count,
                    "pickup_by_user": item.pickup_by_user,
                }
                for item in result
            ]

            total_query = self.db.query(Sampah).join(
                SampahItem, Sampah.id == SampahItem.sampahId
            )

            if status == "collected":
                total_query = total_query.filter(Sampah.isPickup == True)
            elif status == "uncollected":
                total_query = total_query.filter(Sampah.isPickup == False)

            if data_type == "garbage_pile":
                total_query = total_query.filter(Sampah.isGarbagePile == True)
            elif data_type == "garbage_pcs":
                total_query = total_query.filter(Sampah.isGarbagePile == False)

            total_count = total_query.group_by(Sampah.id).count()

            return result_list, total_count

        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_data_statistic_timeseries(
        self,
        token,
        data_type: str,
        status: str,
        start_date,
        end_date,
        page: int,
        page_size: int,
    ):
        try:
            query = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.pickupAt.label("pickup_at"),
                    Sampah.captureTime.label("capture_time"),
                    func.count(SampahItem.id).label("waste_count"),
                    Sampah.pickupByUser.label("pickup_by_user"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(
                    (
                        Sampah.pickupAt if status == "collected" else Sampah.captureTime
                    ).between(start_date, end_date)
                )
            )

            if status == "collected":
                query = query.filter(Sampah.isPickup == True)
            elif status == "uncollected":
                query = query.filter(Sampah.isPickup == False)

            if data_type == "garbage_pile":
                query = query.filter(Sampah.isGarbagePile == True)
            elif data_type == "garbage_pcs":
                query = query.filter(Sampah.isGarbagePile == False)

            result = (
                query.group_by(Sampah.id, Sampah.isGarbagePile, Sampah.pickupByUser)
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )

            result_list = [
                {
                    "id": item.id,
                    "is_waste_pile": item.is_waste_pile,
                    "address": item.address,
                    "geom": to_shape(item.geom).wkt,
                    "pickup_at": item.pickup_at,
                    "capture_time": item.capture_time,
                    "waste_count": item.waste_count,
                    "pickup_by_user": item.pickup_by_user,
                }
                for item in result
            ]

            total_query = self.db.query(Sampah).join(
                SampahItem, Sampah.id == SampahItem.sampahId
            )

            if status == "collected":
                total_query = total_query.filter(Sampah.isPickup == True)
            elif status == "uncollected":
                total_query = total_query.filter(Sampah.isPickup == False)

            if data_type == "garbage_pile":
                total_query = total_query.filter(Sampah.isGarbagePile == True)
            elif data_type == "garbage_pcs":
                total_query = total_query.filter(Sampah.isGarbagePile == False)

            total_count = total_query.group_by(Sampah.id).count()

            return result_list, total_count

        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

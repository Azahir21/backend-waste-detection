import datetime
from fastapi import Depends, HTTPException
from config.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import String, cast, or_, select, func, and_
from sqlalchemy.exc import SQLAlchemyError
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
        self,
        token,
        data_type: str,
        status: str,
        start_date: datetime,
        end_date: datetime,
        sort_by: str,
        sort_order: str,
        search: str,
        page: int,
        page_size: int,
    ):
        try:
            # Build base query with join and aggregate
            query = self.db.query(
                Sampah.id,
                Sampah.isGarbagePile.label("is_waste_pile"),
                Sampah.address,
                Sampah.geom,
                Sampah.pickupAt.label("pickup_at"),
                Sampah.captureTime.label("capture_time"),
                func.count(SampahItem.id).label("waste_count"),
                Sampah.pickupByUser.label("pickup_by_user"),
                Sampah.isPickup.label("pickup_status"),
            ).join(SampahItem, Sampah.id == SampahItem.sampahId)

            # Filter by status
            if status == "collected":
                query = query.filter(Sampah.isPickup == True)
            elif status == "uncollected":
                query = query.filter(Sampah.isPickup == False)

            # Filter by data type
            if data_type == "garbage_pile":
                query = query.filter(Sampah.isGarbagePile == True)
            elif data_type == "garbage_pcs":
                query = query.filter(Sampah.isGarbagePile == False)

            # Filter by capture time start and/or end date
            if start_date:
                query = query.filter(Sampah.captureTime >= start_date)
            if end_date:
                query = query.filter(Sampah.captureTime <= end_date)

            # Group by all non-aggregated fields
            query = query.group_by(
                Sampah.id,
                Sampah.isGarbagePile,
                Sampah.address,
                Sampah.geom,
                Sampah.pickupAt,
                Sampah.captureTime,
                Sampah.pickupByUser,
                Sampah.isPickup,
            )

            # Apply search filter if provided (search across multiple fields)
            if search:
                search_expr = f"%{search}%"
                query = query.having(
                    or_(
                        cast(Sampah.isGarbagePile, String).ilike(search_expr),
                        Sampah.address.ilike(search_expr),
                        cast(Sampah.isPickup, String).ilike(search_expr),
                        cast(Sampah.captureTime, String).ilike(search_expr),
                        cast(func.count(SampahItem.id), String).ilike(search_expr),
                        Sampah.pickupByUser.ilike(search_expr),
                        cast(Sampah.pickupAt, String).ilike(search_expr),
                    )
                )

            # Define sort mapping for allowed fields
            sort_mapping = {
                "id": Sampah.id,
                "is_waste_pile": Sampah.isGarbagePile,
                "address": Sampah.address,
                "pickup_status": Sampah.isPickup,
                "capture_time": Sampah.captureTime,
                "waste_count": func.count(SampahItem.id),
                "pickup_by_user": Sampah.pickupByUser,
                "pickup_at": Sampah.pickupAt,
            }
            sort_col = sort_mapping.get(sort_by, Sampah.id)
            order_clause = (
                sort_col.asc() if sort_order.lower() == "asc" else sort_col.desc()
            )
            query = query.order_by(order_clause, Sampah.id.desc())

            # Create a subquery to count total matching groups
            subq = query.subquery()
            total_count = self.db.query(func.count()).select_from(subq).scalar()

            if total_count == 0:
                raise HTTPException(status_code=404, detail="No data found")

            # Apply pagination
            result = query.offset((page - 1) * page_size).limit(page_size).all()

            # Format the result list
            result_list = [
                {
                    "id": item.id,
                    "is_waste_pile": item.is_waste_pile,
                    "address": item.address,
                    "geom": to_shape(item.geom).wkt if item.geom else None,
                    "pickup_at": item.pickup_at,
                    "capture_time": item.capture_time,
                    "waste_count": item.waste_count,
                    "pickup_by_user": item.pickup_by_user,
                    "pickup_status": item.pickup_status,
                }
                for item in result
            ]

            return result_list, total_count

        except SQLAlchemyError as e:
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
                .order_by(Sampah.id.desc())
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

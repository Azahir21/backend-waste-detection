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

    async def get_all_statistic(self, token):
        try:
            # Query for collected waste statistics
            collected_waste = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.pickupAt,
                    func.count(SampahItem.id).label("waste_count"),
                    Sampah.pickupByUser.label("pickup_by_user"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(Sampah.isPickup == True)
                .group_by(Sampah.id, Sampah.pickupByUser, Sampah.isGarbagePile)
                .all()
            )

            collected_list = [
                WasteCollected(
                    id=item.id,
                    is_waste_pile=item.is_waste_pile,
                    address=item.address,
                    geom=to_shape(item.geom).wkt,
                    pickupAt=item.pickupAt,
                    waste_count=item.waste_count,
                    pickup_by_user=item.pickup_by_user,
                )
                for item in collected_waste
            ]

            # Query for not collected waste statistics
            not_collected_waste = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.captureTime,
                    func.count(SampahItem.id).label("waste_count"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(Sampah.isPickup == False)
                .group_by(Sampah.id, Sampah.isGarbagePile)
                .all()
            )

            not_collected_list = [
                WasteNotCollected(
                    id=item.id,
                    is_waste_pile=item.is_waste_pile,
                    address=item.address,
                    geom=to_shape(item.geom).wkt,
                    captureTime=item.captureTime,
                    waste_count=item.waste_count,
                )
                for item in not_collected_waste
            ]

            # Calculate totals
            total_waste_collected = len(collected_list)
            total_waste_not_collected = len(not_collected_list)

            # Return the result in the expected schema
            return StatisticOutput(
                total_waste_collected=total_waste_collected,
                total_waste_not_collected=total_waste_not_collected,
                collected=collected_list,
                not_collected=not_collected_list,
            )

        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_all_statistic_timeseries(self, token, start_date, end_date):
        try:
            # Query for collected waste statistics within date range
            collected_waste = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.pickupAt,
                    func.count(SampahItem.id).label("waste_count"),
                    Sampah.pickupByUser.label("pickup_by_user"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(
                    Sampah.isPickup == True,
                    Sampah.pickupAt.between(start_date, end_date),
                )
                .group_by(Sampah.id, Sampah.pickupByUser, Sampah.isGarbagePile)
                .all()
            )

            collected_list = [
                WasteCollected(
                    id=item.id,
                    is_waste_pile=item.is_waste_pile,
                    address=item.address,
                    geom=to_shape(item.geom).wkt,
                    pickupAt=item.pickupAt,
                    waste_count=item.waste_count,
                    pickup_by_user=item.pickup_by_user,
                )
                for item in collected_waste
            ]

            # Query for not collected waste statistics within date range
            not_collected_waste = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.captureTime,
                    func.count(SampahItem.id).label("waste_count"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(
                    Sampah.isPickup == False,
                    Sampah.captureTime.between(start_date, end_date),
                )
                .group_by(Sampah.id, Sampah.isGarbagePile)
                .all()
            )

            not_collected_list = [
                WasteNotCollected(
                    id=item.id,
                    is_waste_pile=item.is_waste_pile,
                    address=item.address,
                    geom=to_shape(item.geom).wkt,
                    captureTime=item.captureTime,
                    waste_count=item.waste_count,
                )
                for item in not_collected_waste
            ]

            # Calculate totals
            total_waste_collected = len(collected_list)
            total_waste_not_collected = len(not_collected_list)

            # Return the result in the expected schema
            return StatisticOutput(
                total_waste_collected=total_waste_collected,
                total_waste_not_collected=total_waste_not_collected,
                collected=collected_list,
                not_collected=not_collected_list,
            )

        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_garbage_pile_statistic(self, token):
        try:
            # Query for collected garbage pile statistics
            collected_waste = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.pickupAt,
                    func.count(SampahItem.id).label("waste_count"),
                    Sampah.pickupByUser.label("pickup_by_user"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(Sampah.isPickup == True, Sampah.isGarbagePile == True)
                .group_by(Sampah.id, Sampah.pickupByUser, Sampah.isGarbagePile)
                .all()
            )

            collected_list = [
                WasteCollected(
                    id=item.id,
                    is_waste_pile=item.is_waste_pile,
                    address=item.address,
                    geom=to_shape(item.geom).wkt,
                    pickupAt=item.pickupAt,
                    waste_count=item.waste_count,
                    pickup_by_user=item.pickup_by_user,
                )
                for item in collected_waste
            ]

            # Query for not collected garbage pile statistics
            not_collected_waste = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.captureTime,
                    func.count(SampahItem.id).label("waste_count"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(Sampah.isPickup == False, Sampah.isGarbagePile == True)
                .group_by(Sampah.id, Sampah.isGarbagePile)
                .all()
            )

            not_collected_list = [
                WasteNotCollected(
                    id=item.id,
                    is_waste_pile=item.is_waste_pile,
                    address=item.address,
                    geom=to_shape(item.geom).wkt,
                    captureTime=item.captureTime,
                    waste_count=item.waste_count,
                )
                for item in not_collected_waste
            ]

            # Calculate totals
            total_waste_collected = len(collected_list)
            total_waste_not_collected = len(not_collected_list)

            # Return the result in the expected schema
            return StatisticOutput(
                total_waste_collected=total_waste_collected,
                total_waste_not_collected=total_waste_not_collected,
                collected=collected_list,
                not_collected=not_collected_list,
            )

        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_garbage_pile_statistic_timeseries(self, token, start_date, end_date):
        try:
            # Query for collected garbage pile statistics within date range
            collected_waste = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.pickupAt,
                    func.count(SampahItem.id).label("waste_count"),
                    Sampah.pickupByUser.label("pickup_by_user"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(
                    Sampah.isPickup == True,
                    Sampah.isGarbagePile == True,
                    Sampah.pickupAt.between(start_date, end_date),
                )
                .group_by(Sampah.id, Sampah.pickupByUser, Sampah.isGarbagePile)
                .all()
            )

            collected_list = [
                WasteCollected(
                    id=item.id,
                    is_waste_pile=item.is_waste_pile,
                    address=item.address,
                    geom=to_shape(item.geom).wkt,
                    pickupAt=item.pickupAt,
                    waste_count=item.waste_count,
                    pickup_by_user=item.pickup_by_user,
                )
                for item in collected_waste
            ]

            # Query for not collected garbage pile statistics within date range
            not_collected_waste = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.captureTime,
                    func.count(SampahItem.id).label("waste_count"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(
                    Sampah.isPickup == False,
                    Sampah.isGarbagePile == True,
                    Sampah.captureTime.between(start_date, end_date),
                )
                .group_by(Sampah.id, Sampah.isGarbagePile)
                .all()
            )

            not_collected_list = [
                WasteNotCollected(
                    id=item.id,
                    is_waste_pile=item.is_waste_pile,
                    address=item.address,
                    geom=to_shape(item.geom).wkt,
                    captureTime=item.captureTime,
                    waste_count=item.waste_count,
                )
                for item in not_collected_waste
            ]

            # Calculate totals
            total_waste_collected = len(collected_list)
            total_waste_not_collected = len(not_collected_list)

            # Return the result in the expected schema
            return StatisticOutput(
                total_waste_collected=total_waste_collected,
                total_waste_not_collected=total_waste_not_collected,
                collected=collected_list,
                not_collected=not_collected_list,
            )

        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_garbage_pcs_statistic(self, token):
        try:
            # Query for collected garbage pcs statistics
            collected_waste = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.pickupAt,
                    func.count(SampahItem.id).label("waste_count"),
                    Sampah.pickupByUser.label("pickup_by_user"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(Sampah.isPickup == True, Sampah.isGarbagePile == False)
                .group_by(Sampah.id, Sampah.pickupByUser, Sampah.isGarbagePile)
                .all()
            )

            collected_list = [
                WasteCollected(
                    id=item.id,
                    is_waste_pile=item.is_waste_pile,
                    address=item.address,
                    geom=to_shape(item.geom).wkt,
                    pickupAt=item.pickupAt,
                    waste_count=item.waste_count,
                    pickup_by_user=item.pickup_by_user,
                )
                for item in collected_waste
            ]

            # Query for not collected garbage pcs statistics
            not_collected_waste = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.captureTime,
                    func.count(SampahItem.id).label("waste_count"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(Sampah.isPickup == False, Sampah.isGarbagePile == False)
                .group_by(Sampah.id, Sampah.isGarbagePile)
                .all()
            )

            not_collected_list = [
                WasteNotCollected(
                    id=item.id,
                    is_waste_pile=item.is_waste_pile,
                    address=item.address,
                    geom=to_shape(item.geom).wkt,
                    captureTime=item.captureTime,
                    waste_count=item.waste_count,
                )
                for item in not_collected_waste
            ]

            # Calculate totals
            total_waste_collected = len(collected_list)
            total_waste_not_collected = len(not_collected_list)

            # Return the result in the expected schema
            return StatisticOutput(
                total_waste_collected=total_waste_collected,
                total_waste_not_collected=total_waste_not_collected,
                collected=collected_list,
                not_collected=not_collected_list,
            )

        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_garbage_pcs_statistic_timeseries(self, token, start_date, end_date):
        try:
            # Query for collected garbage pcs statistics within date range
            collected_waste = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.pickupAt,
                    func.count(SampahItem.id).label("waste_count"),
                    Sampah.pickupByUser.label("pickup_by_user"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(
                    Sampah.isPickup == True,
                    Sampah.isGarbagePile == False,
                    Sampah.pickupAt.between(start_date, end_date),
                )
                .group_by(Sampah.id, Sampah.pickupByUser, Sampah.isGarbagePile)
                .all()
            )

            collected_list = [
                WasteCollected(
                    id=item.id,
                    is_waste_pile=item.is_waste_pile,
                    address=item.address,
                    geom=to_shape(item.geom).wkt,
                    pickupAt=item.pickupAt,
                    waste_count=item.waste_count,
                    pickup_by_user=item.pickup_by_user,
                )
                for item in collected_waste
            ]

            # Query for not collected garbage pcs statistics within date range
            not_collected_waste = (
                self.db.query(
                    Sampah.id,
                    Sampah.isGarbagePile.label("is_waste_pile"),
                    Sampah.address,
                    Sampah.geom,
                    Sampah.captureTime,
                    func.count(SampahItem.id).label("waste_count"),
                )
                .join(SampahItem, Sampah.id == SampahItem.sampahId)
                .filter(
                    Sampah.isPickup == False,
                    Sampah.isGarbagePile == False,
                    Sampah.captureTime.between(start_date, end_date),
                )
                .group_by(Sampah.id, Sampah.isGarbagePile)
                .all()
            )

            not_collected_list = [
                WasteNotCollected(
                    id=item.id,
                    is_waste_pile=item.is_waste_pile,
                    address=item.address,
                    geom=to_shape(item.geom).wkt,
                    captureTime=item.captureTime,
                    waste_count=item.waste_count,
                )
                for item in not_collected_waste
            ]

            # Calculate totals
            total_waste_collected = len(collected_list)
            total_waste_not_collected = len(not_collected_list)

            # Return the result in the expected schema
            return StatisticOutput(
                total_waste_collected=total_waste_collected,
                total_waste_not_collected=total_waste_not_collected,
                collected=collected_list,
                not_collected=not_collected_list,
            )

        except Exception as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

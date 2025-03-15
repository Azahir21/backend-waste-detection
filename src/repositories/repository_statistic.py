import datetime
from fastapi import Depends, HTTPException
from config.database import get_db
from sqlalchemy import Integer, String, cast, or_, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from geoalchemy2.shape import to_shape

from config.models.sampah_item_model import SampahItem
from config.models.sampah_model import Sampah
from config.schemas.common_schema import TokenData


class StatisticRepository:
    def __init__(
        self,
        db: Session = Depends(get_db),
    ):
        self.db = db

    DATABASE_ERROR_MESSAGE = "Database error"

    async def get_total_statistic(self, token):
        try:
            # Original queries for totals
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

            # New: Historical data for the past 3 months (cumulative per week)
            three_months_ago = datetime.datetime.now(
                datetime.timezone.utc
            ) - datetime.timedelta(days=90)
            # Compute the Monday (week start) for the three_months_ago date
            period_start = three_months_ago - datetime.timedelta(
                days=three_months_ago.weekday()
            )

            # Truncate pickupAt to Monday (ensuring weeks run Monday to Sunday)
            week_start_expr = func.date_trunc("week", Sampah.pickupAt)
            # Compute relative week index:
            #   Difference in seconds between week_start and period_start, divided by seconds per week, plus 1
            relative_week_index_expr = (
                func.floor(
                    func.extract("epoch", week_start_expr - period_start)
                    / (7 * 24 * 60 * 60)
                )
                + 1
            )

            # For display, also compute the month name
            month_expr = func.to_char(Sampah.pickupAt, "Month")
            # Compute week in month using ISO week numbers:
            iso_week_index_expr = func.cast(
                func.to_char(week_start_expr, "IW"), Integer
            )
            first_week_expr = func.date_trunc(
                "week", func.date_trunc("month", Sampah.pickupAt)
            )
            first_week_index_expr = func.cast(
                func.to_char(first_week_expr, "IW"), Integer
            )
            week_in_month_expr = iso_week_index_expr - first_week_index_expr + 1

            historical_data = (
                self.db.query(
                    relative_week_index_expr.label("week_index"),
                    month_expr.label("month_name"),
                    week_in_month_expr.label("week_in_month"),
                    func.count(Sampah.id).label("total_transported"),
                )
                .filter(
                    Sampah.isPickup == True,
                    Sampah.pickupAt.isnot(None),
                    Sampah.pickupAt >= three_months_ago,
                )
                .group_by(relative_week_index_expr, month_expr, week_in_month_expr)
                .order_by(relative_week_index_expr)
                .all()
            )

            # Map the aggregated results by their week index
            aggregated = {int(item.week_index): item for item in historical_data}

            # Determine the last week in the period (Monday of current week)
            now = datetime.datetime.now(datetime.timezone.utc)
            current_week = now - datetime.timedelta(days=now.weekday())

            # Build a complete list of weeks from period_start to current_week
            week_list = []
            current_date = period_start
            week_idx = 1
            while current_date <= current_week:
                # For display, compute month name from the week start date
                month_name = current_date.strftime("%B")
                # Compute the first Monday of the month for this week
                first_day_of_month = current_date.replace(day=1)
                first_monday = first_day_of_month - datetime.timedelta(
                    days=first_day_of_month.weekday()
                )
                week_in_month = (current_date - first_monday).days // 7

                if week_idx in aggregated:
                    total_transported = aggregated[week_idx].total_transported
                else:
                    total_transported = 0

                week_list.append(
                    {
                        "week_index": week_idx,
                        "month_name": month_name,
                        "week_in_month": week_in_month,
                        "total_transported": total_transported,
                    }
                )
                week_idx += 1
                current_date += datetime.timedelta(days=7)

            return {
                "collected_garbage_pile": query_collected_garbage_pile,
                "collected_garbage_pcs": query_collected_garbage_pcs,
                "not_collected_garbage_pile": query_not_collected_garbage_pile,
                "not_collected_garbage_pcs": query_not_collected_garbage_pcs,
                "historical_data": week_list,
            }

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
                Sampah.imagePath.label("image_url"),
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
                "image_url": Sampah.imagePath,
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
                    "image_url": (
                        f"https://jjmbm5rz-8000.asse.devtunnels.ms/detected_image/{item.image_url.split('/')[-1]}"
                        if "detected_image" in item.image_url
                        else f"https://jjmbm5rz-8000.asse.devtunnels.ms/garbage-image/{item.image_url.split('/')[-1]}"
                    ),
                }
                for item in result
            ]

            return result_list, total_count

        except SQLAlchemyError as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_data_statistic_sheet(
        self,
        token: TokenData,
        data_type: str,
        status: str,
        start_date,
        end_date,
        sort_by: str,
        sort_order: str,
        search: str,
        user: bool,
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
                Sampah.imagePath.label("image_url"),
            ).join(SampahItem, Sampah.id == SampahItem.sampahId)

            # Filter by user if the user parameter is True
            if user:
                query = query.filter(
                    Sampah.isPickup == True, Sampah.pickupByUser == token.name
                )
            # Otherwise apply standard status filter
            else:
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
                Sampah.imagePath,  # Add image path to group by
            )

            # Apply search filter if provided (search only on address)
            if search:
                search_expr = f"%{search}%"
                query = query.having(Sampah.address.ilike(search_expr))

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
                "image_url": Sampah.imagePath,
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

            # Get all results
            result = query.all()

            # Format the result list
            result_list = []
            for item in result:
                # Extract coordinates from WKT format if geom exists
                maps_link = None
                if item.geom:
                    # Convert geometry to WKT
                    wkt = to_shape(item.geom).wkt
                    # Extract coordinates from WKT (format is typically "POINT(lon lat)")
                    if wkt.startswith("POINT"):
                        # Extract coordinates between parentheses
                        coords = wkt.split("(")[1].split(")")[0]
                        # Split by space and reverse order to get lat,lng format
                        lon, lat = coords.split()
                        # Create Google Maps link
                        maps_link = f"https://www.google.com/maps/place/{lat},{lon}"

                result_list.append(
                    {
                        "id": item.id,
                        "waste type": (
                            "Garbage Pile" if item.is_waste_pile else "Garbage Pieces"
                        ),
                        "address": item.address,
                        "geom": to_shape(item.geom).wkt if item.geom else None,
                        "pickup at": item.pickup_at,
                        "capture time": item.capture_time,
                        "waste count": item.waste_count,
                        "pickup by user": item.pickup_by_user,
                        "pickup status": (
                            "Collected" if item.pickup_status else "Not Collected"
                        ),
                        "Waste Location": maps_link,
                        "image_url": (
                            f"http://localhost:8000/detected_image/{item.image_url.split('/')[-1]}"
                            if "detected_image" in item.image_url
                            else f"http://localhost:8000/garbage-image/{item.image_url.split('/')[-1]}"
                        ),
                    }
                )

            return result_list

        except SQLAlchemyError as e:
            print(f"Error: {e}")
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

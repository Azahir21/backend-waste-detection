import calendar
from datetime import date, timedelta
from fastapi import Depends, HTTPException
from sqlalchemy import Date, case, cast, func, literal_column
from config.database import get_db
from config.models import point_model, sampah_model
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from config.models.user_model import User


class PointRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    DATABASE_ERROR_MESSAGE = "Database error"

    async def get_current_user_point(self, user_id: int):
        try:
            return (
                self.db.query(point_model.Point)
                .filter(point_model.Point.userId == user_id)
                .first()
            )
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def update_user_point(self, user_id: int, point: int):
        try:
            user_point = await self.get_current_user_point(user_id)
            user_point.point += point
            self.db.commit()
            self.db.refresh(user_point)
            return user_point
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_today_point(self, querying_user_id: int):
        try:
            # specific_date = date(2024, 6, 12)  # Ganti dengan tanggal yang diinginkan
            specific_date = date.today()

            # Subquery untuk menghitung poin harian
            daily_points_subquery = (
                self.db.query(
                    sampah_model.Sampah.userId,
                    func.coalesce(func.sum(sampah_model.Sampah.point), 0).label(
                        "daily_points"
                    ),
                )
                .filter(cast(sampah_model.Sampah.captureTime, Date) == specific_date)
                .group_by(sampah_model.Sampah.userId)
                .subquery()
            )

            # Query utama dengan peringkat
            ranked_users = (
                self.db.query(
                    User.id.label("user_id"),
                    User.username,
                    func.coalesce(daily_points_subquery.c.daily_points, 0).label(
                        "total_points"
                    ),
                    func.row_number()
                    .over(
                        order_by=(
                            func.coalesce(
                                daily_points_subquery.c.daily_points, 0
                            ).desc(),
                            User.id,
                        )
                    )
                    .label("ranking"),
                    case(
                        (User.id == querying_user_id, literal_column("'true'")),
                        else_=literal_column("'false'"),
                    ).label("is_querying_user"),
                )
                .outerjoin(
                    daily_points_subquery, User.id == daily_points_subquery.c.userId
                )
                .order_by(
                    func.coalesce(daily_points_subquery.c.daily_points, 0).desc(),
                    User.id,
                )
                .subquery()
            )

            # Final query to get top 10 and querying user
            result = (
                self.db.query(ranked_users)
                .filter(
                    (ranked_users.c.ranking <= 10)
                    | (ranked_users.c.is_querying_user == "true")
                )
                .order_by(ranked_users.c.ranking)
                .all()
            )

            return [
                {
                    "user_id": row.user_id,
                    "username": row.username,
                    "total_points": row.total_points,
                    "ranking": row.ranking,
                    "is_querying_user": row.is_querying_user == "true",
                }
                for row in result
            ]

        except SQLAlchemyError as e:
            # Handle SQLAlchemy exceptions
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_all_users_weekly_points_and_ranking(self, querying_user_id: int):
        try:
            # Calculate start_date as the Monday of the current week and end_date as the Sunday
            today = date.today()  # Example date, which is a Sunday
            start_date = today - timedelta(
                days=(today.weekday())
            )  # Correct calculation for Monday
            end_date = start_date + timedelta(days=6)  # Sunday of the same week

            print(start_date, end_date)

            # Subquery to calculate weekly points per user
            subquery = (
                self.db.query(
                    sampah_model.Sampah.userId,
                    func.coalesce(func.sum(sampah_model.Sampah.point), 0).label(
                        "weekly_points"
                    ),
                )
                .filter(
                    cast(sampah_model.Sampah.captureTime, Date).between(
                        start_date, end_date
                    )
                )
                .group_by(sampah_model.Sampah.userId)
                .subquery()
            )

            # Main query with ranking
            ranked_users = (
                self.db.query(
                    User.id.label("user_id"),
                    User.username,
                    func.coalesce(subquery.c.weekly_points, 0).label("total_points"),
                    func.row_number()
                    .over(
                        order_by=(
                            func.coalesce(subquery.c.weekly_points, 0).desc(),
                            User.id,
                        )
                    )
                    .label("ranking"),
                    case(
                        (User.id == querying_user_id, literal_column("'true'")),
                        else_=literal_column("'false'"),
                    ).label("is_querying_user"),
                )
                .outerjoin(subquery, User.id == subquery.c.userId)
                .order_by(func.coalesce(subquery.c.weekly_points, 0).desc(), User.id)
                .subquery()
            )

            # Final query to get top 10 users and querying user
            result = (
                self.db.query(ranked_users)
                .filter(
                    (ranked_users.c.ranking <= 10)
                    | (ranked_users.c.is_querying_user == "true")
                )
                .order_by(ranked_users.c.ranking)
                .all()
            )

            return [
                {
                    "user_id": row.user_id,
                    "username": row.username,
                    "total_points": row.total_points,
                    "ranking": row.ranking,
                    "is_querying_user": row.is_querying_user == "true",
                }
                for row in result
            ]

        except SQLAlchemyError as e:
            # Handle SQLAlchemy exceptions
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_all_users_monthly_points_and_ranking(self, querying_user_id: int):
        try:
            # Get the first and last day of the current month
            today = date.today()
            start_date = today.replace(day=1)  # 1st day of the current month

            # Calculate the last day of the current month
            _, last_day = calendar.monthrange(today.year, today.month)
            end_date = today.replace(day=last_day)  # Last day of the current month

            # Subquery to calculate monthly points per user
            subquery = (
                self.db.query(
                    sampah_model.Sampah.userId,
                    func.coalesce(func.sum(sampah_model.Sampah.point), 0).label(
                        "monthly_points"
                    ),
                )
                .filter(
                    cast(sampah_model.Sampah.captureTime, Date).between(
                        start_date, end_date
                    )
                )
                .group_by(sampah_model.Sampah.userId)
                .subquery()
            )

            # Main query with ranking
            ranked_users = (
                self.db.query(
                    User.id.label("user_id"),
                    User.username,
                    func.coalesce(subquery.c.monthly_points, 0).label("total_points"),
                    func.row_number()
                    .over(
                        order_by=(
                            func.coalesce(subquery.c.monthly_points, 0).desc(),
                            User.id,
                        )
                    )
                    .label("ranking"),
                    case(
                        (User.id == querying_user_id, literal_column("'true'")),
                        else_=literal_column("'false'"),
                    ).label("is_querying_user"),
                )
                .outerjoin(subquery, User.id == subquery.c.userId)
                .order_by(func.coalesce(subquery.c.monthly_points, 0).desc(), User.id)
                .subquery()
            )

            # Final query to get top 10 users and querying user
            result = (
                self.db.query(ranked_users)
                .filter(
                    (ranked_users.c.ranking <= 10)
                    | (ranked_users.c.is_querying_user == "true")
                )
                .order_by(ranked_users.c.ranking)
                .all()
            )

            return [
                {
                    "user_id": row.user_id,
                    "username": row.username,
                    "total_points": row.total_points,
                    "ranking": row.ranking,
                    "is_querying_user": row.is_querying_user == "true",
                }
                for row in result
            ]

        except SQLAlchemyError as e:
            # Handle SQLAlchemy exceptions
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_all_users_points_and_ranking(self, querying_user_id: int):
        try:
            # Subquery to calculate total points for all users
            subquery = (
                self.db.query(
                    sampah_model.Sampah.userId,
                    func.coalesce(func.sum(sampah_model.Sampah.point), 0).label(
                        "total_points"
                    ),
                )
                .group_by(sampah_model.Sampah.userId)
                .subquery()
            )

            # Main query with ranking
            ranked_users = (
                self.db.query(
                    User.id.label("user_id"),
                    User.username,
                    func.coalesce(subquery.c.total_points, 0).label("total_points"),
                    func.row_number()
                    .over(
                        order_by=(
                            func.coalesce(subquery.c.total_points, 0).desc(),
                            User.id,
                        )
                    )
                    .label("ranking"),
                    case(
                        (User.id == querying_user_id, literal_column("'true'")),
                        else_=literal_column("'false'"),
                    ).label("is_querying_user"),
                )
                .outerjoin(subquery, User.id == subquery.c.userId)
                .order_by(func.coalesce(subquery.c.total_points, 0).desc(), User.id)
                .subquery()
            )

            # Final query to get top 10 users and querying user
            result = (
                self.db.query(ranked_users)
                .filter(
                    (ranked_users.c.ranking <= 10)
                    | (ranked_users.c.is_querying_user == "true")
                )
                .order_by(ranked_users.c.ranking)
                .all()
            )

            return [
                {
                    "user_id": row.user_id,
                    "username": row.username,
                    "total_points": row.total_points,
                    "ranking": row.ranking,
                    "is_querying_user": row.is_querying_user == "true",
                }
                for row in result
            ]

        except SQLAlchemyError as e:
            # Handle SQLAlchemy exceptions
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_all_user_point_timeseries(
        self,
        start_date: str = None,
        end_date: str = None,
        querying_user_id: int = None,
    ):
        try:
            # Parse start_date and end_date
            start_date = date.fromisoformat(start_date) if start_date else None
            end_date = date.fromisoformat(end_date) if end_date else None

            subquery = (
                self.db.query(
                    sampah_model.Sampah.userId,
                    func.coalesce(func.sum(sampah_model.Sampah.point), 0).label(
                        "weekly_points"
                    ),
                )
                .filter(
                    cast(sampah_model.Sampah.captureTime, Date).between(
                        start_date, end_date
                    )
                )
                .group_by(sampah_model.Sampah.userId)
                .subquery()
            )

            # Main query with ranking
            ranked_users = (
                self.db.query(
                    User.id.label("user_id"),
                    User.username,
                    func.coalesce(subquery.c.weekly_points, 0).label("total_points"),
                    func.row_number()
                    .over(
                        order_by=(
                            func.coalesce(subquery.c.weekly_points, 0).desc(),
                            User.id,
                        )
                    )
                    .label("ranking"),
                    case(
                        (User.id == querying_user_id, literal_column("'true'")),
                        else_=literal_column("'false'"),
                    ).label("is_querying_user"),
                )
                .outerjoin(subquery, User.id == subquery.c.userId)
                .order_by(func.coalesce(subquery.c.weekly_points, 0).desc(), User.id)
                .subquery()
            )

            # Final query to get top 10 users and querying user
            result = (
                self.db.query(ranked_users)
                .filter(
                    (ranked_users.c.ranking <= 10)
                    | (ranked_users.c.is_querying_user == "true")
                )
                .order_by(ranked_users.c.ranking)
                .all()
            )

            return [
                {
                    "user_id": row.user_id,
                    "username": row.username,
                    "total_points": row.total_points,
                    "ranking": row.ranking,
                    "is_querying_user": row.is_querying_user == "true",
                }
                for row in result
            ]

        except SQLAlchemyError as e:
            # Handle SQLAlchemy exceptions
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

from fastapi import Depends, HTTPException
from config.database import get_db
from config.models import point_model
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


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

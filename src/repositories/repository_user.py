from datetime import datetime
from fastapi import Depends, HTTPException
from config.database import get_db
from config.models import user_model, point_model
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


class UserRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    DATABASE_ERROR_MESSAGE = "Database error"

    async def insert_new_user(self, user: user_model.User):
        try:
            new_user = user_model.User(
                **user.dict(),
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
            )
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            init_point = point_model.Point(
                userId=new_user.id,
                point=0,
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
            )
            self.db.add(init_point)
            self.db.commit()
            self.db.refresh(init_point)
            return new_user
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def find_user_by_username(self, username: str):
        try:
            return (
                self.db.query(user_model.User)
                .filter(user_model.User.username == username)
                .first()
            )
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def find_user_by_email(self, email: str):
        try:
            data = (
                self.db.query(user_model.User)
                .filter(user_model.User.email == email)
                .first()
            )
            return data
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

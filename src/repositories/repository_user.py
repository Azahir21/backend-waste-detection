from datetime import datetime
from fastapi import Depends, HTTPException
from config.database import get_db
from config.models import user_model, point_model
from sqlalchemy import or_, cast, String
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
                badgeId=1,
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

    async def deactivate_user(self, id: int):
        try:
            user = (
                self.db.query(user_model.User).filter(user_model.User.id == id).first()
            )

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            if user.role == "admin":
                raise HTTPException(
                    status_code=403, detail="Admin cannot be deactivated"
                )

            if user.role == "user":
                raise HTTPException(
                    status_code=403, detail="User cannot be deactivated"
                )

            user.active = not user.active
            self.db.commit()
            return user
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def reset_password(self, id: int, password: str):
        try:
            user = (
                self.db.query(user_model.User).filter(user_model.User.id == id).first()
            )

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            user.password = password
            self.db.commit()
            return user
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    async def get_all_user(
        self, page: int, page_size: int, sort_by: str, sort_order: str, search: str
    ):
        try:
            offset = (page - 1) * page_size
            query = self.db.query(user_model.User)

            # Apply search filter if provided (searching across multiple fields)
            if search:
                search_expr = f"%{search}%"
                query = query.filter(
                    or_(
                        user_model.User.fullName.ilike(search_expr),
                        user_model.User.jenisKelamin.ilike(search_expr),
                        user_model.User.username.ilike(search_expr),
                        user_model.User.email.ilike(search_expr),
                        user_model.User.role.ilike(search_expr),
                        cast(user_model.User.active, String).ilike(search_expr),
                    )
                )

            # Define sort mapping for allowed fields
            sort_mapping = {
                "id": user_model.User.id,
                "fullname": user_model.User.fullName,
                "gender": user_model.User.jenisKelamin,
                "username": user_model.User.username,
                "email": user_model.User.email,
                "role": user_model.User.role,
                "status": user_model.User.active,
            }
            # Use lower-case key to match mapping; default to id if key is not valid.
            sort_col = sort_mapping.get(sort_by.lower(), user_model.User.id)
            # Apply primary sort, then a secondary sort by id descending to ensure consistent order
            if sort_order.lower() == "asc":
                query = query.order_by(sort_col.asc(), user_model.User.id.desc())
            else:
                query = query.order_by(sort_col.desc(), user_model.User.id.desc())

            total_count = query.count()
            users = query.offset(offset).limit(page_size).all()
            return users, total_count
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

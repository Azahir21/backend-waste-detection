from sqlalchemy import Column, String, BigInteger, DateTime, Boolean
from sqlalchemy.orm import validates, relationship
from datetime import datetime
from config.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    fullName = Column(String)
    jenisKelamin = Column(String)
    noTelp = Column(String)
    alamat = Column(String)
    createdAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    role = Column(String, nullable=False, default="user")
    active = Column(Boolean, nullable=False, default="true")

    points = relationship(
        "Point", back_populates="user", cascade="all, delete, delete-orphan"
    )
    sampahs = relationship(
        "Sampah", back_populates="user", cascade="all, delete, delete-orphan"
    )

    @validates("email")
    def validate_email(self, key, address):
        assert "@" in address, "Provided email is not valid"
        return address

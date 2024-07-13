from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class Point(Base):
    __tablename__ = "points"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    userId = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    point = Column(BigInteger, nullable=False)
    createdAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = relationship("User", back_populates="points")

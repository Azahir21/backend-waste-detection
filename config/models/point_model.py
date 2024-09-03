from sqlalchemy import Column, BigInteger, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class Point(Base):
    __tablename__ = "points"  # Use double underscores for __tablename__

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    userId = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    point = Column(BigInteger, nullable=False)
    createdAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    badgeId = Column(Integer, ForeignKey("badges.id"), nullable=True)

    user = relationship("User", back_populates="points")
    badges = relationship("Badge", back_populates="points")  # String reference here

from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import validates, relationship
from geoalchemy2.types import Geometry
from datetime import datetime
from config.database import Base


class Sampah(Base):
    __tablename__ = "sampahs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    userId = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    address = Column(String, nullable=False)
    geom = Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True))
    imagePath = Column(String)
    captureTime = Column(DateTime)
    point = Column(BigInteger, nullable=False)
    createdAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    sampah_items = relationship("SampahItem", back_populates="sampah")
    user = relationship("User", back_populates="sampahs")

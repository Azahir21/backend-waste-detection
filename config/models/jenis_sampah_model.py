from sqlalchemy import Column, String, BigInteger, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class JenisSampah(Base):
    __tablename__ = "jenis_sampahs"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    nama = Column(String, nullable=False)
    point = Column(BigInteger, nullable=False)
    createdAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    sampah_items = relationship("SampahItem", back_populates="jenis_sampah")

from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class SampahItem(Base):
    __tablename__ = "sampah_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    sampahId = Column(BigInteger, ForeignKey("sampahs.id"), nullable=False)
    jenisSampahId = Column(BigInteger, ForeignKey("jenis_sampahs.id"), nullable=False)
    createdAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    sampah = relationship("Sampah", back_populates="sampah_items")
    jenis_sampah = relationship("JenisSampah", back_populates="sampah_items")

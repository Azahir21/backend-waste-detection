from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from config.database import Base


class Badge(Base):
    __tablename__ = "badges"  # Use double underscores for __tablename__

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    pointMinimum = Column(Integer)
    imageUrl = Column(String(255))

    points = relationship("Point", back_populates="badges")  # String reference here

    def __repr__(self):
        return f"<Badge(id={self.id}, name='{self.name}', pointMinimum={self.pointMinimum})>"

from pydantic import BaseModel
from datetime import datetime


class OutputPoint(BaseModel):
    point: int
    updatedAt: datetime

from pydantic import BaseModel
from datetime import datetime


class OutputPoint(BaseModel):
    point: int
    updatedAt: datetime


class Leaderboard(BaseModel):
    id: int
    username: str
    point: int

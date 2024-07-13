import datetime
from pydantic import BaseModel


class InputArticle(BaseModel):
    title: str
    content: str


class OutputArticle(BaseModel):
    title: str
    content: str
    image: str
    createdAt: datetime.datetime

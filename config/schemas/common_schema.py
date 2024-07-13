from pydantic import BaseModel


class StandardResponse(BaseModel):
    detail: str


class TokenData(BaseModel):
    userID: str
    name: str

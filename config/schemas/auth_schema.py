from typing import Optional
from pydantic import BaseModel, Field


class InputUser(BaseModel):
    fullName: str
    jenisKelamin: str
    username: str
    email: str
    password: str
    role: Optional[str] = Field(default="user")
    active: Optional[bool] = Field(default=True)


class InputLogin(BaseModel):
    email: str
    password: str


class OutputProfile(BaseModel):
    username: str
    email: str


class OutputLogin(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str


class OutputAllUser(BaseModel):
    id: int
    full_name: str
    gender: str
    username: str
    email: str
    role: str
    status: bool


class ForgotPassword(BaseModel):
    username: str
    email: str
    password: str

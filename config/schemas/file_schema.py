import datetime
from typing import Optional
from geoalchemy2.shape import to_shape
from pydantic import BaseModel, field_validator
from pydantic_extra_types.coordinate import Latitude, Longitude


class InputFile(BaseModel):
    garbage_count: Optional[int] = None
    garbage_detected: Optional[int] = None
    garbage_names: Optional[str] = None
    address: Optional[str] = None
    latitude: float
    longitude: float
    capture_date: str


class InputMetadataGarbage(BaseModel):
    garbage_count: Optional[int] = None
    garbage_detected: Optional[int] = None
    garbage_names: Optional[str] = None


class InputLocation(BaseModel):
    address: Optional[str] = None
    geom: str


class OutputLocation(BaseModel):
    address: Optional[str] = None
    geom: str
    latitude: float
    longitude: float


class InputFiletoDB(BaseModel):
    type_id: int
    category_id: int
    description: str
    path: str
    capture_date: datetime.datetime


class OutputFile(BaseModel):
    username: str
    email: str
    garbage_count: Optional[int] = None
    garbage_detected: Optional[int] = None
    garbage_names: Optional[str] = None
    address: Optional[str] = None
    geom: str
    longitude: float
    latitude: float
    description: Optional[str] = None
    caption: Optional[str] = None
    path: str
    capture_date: str

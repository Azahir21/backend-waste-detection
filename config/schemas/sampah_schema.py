from pydantic import BaseModel
from typing import List, Optional
import datetime


class CountObject(BaseModel):
    name: str
    count: int
    point: int


class InputSampahItem(BaseModel):
    jenisSampahId: int


class OutputSampahItem(BaseModel):
    nama: str
    point: int

    class Config:
        from_attributes = True


class InputSampah(BaseModel):
    address: str
    longitude: float
    latitude: float
    point: int
    image: str
    filename: str
    capture_date: datetime.datetime
    sampah_items: List[InputSampahItem]


class OutputSampah(BaseModel):
    id: int
    address: str
    captureTime: datetime.datetime
    point: int

    class Config:
        from_attributes = True


class OutputSampahDetail(BaseModel):
    id: int
    is_waste_pile: bool
    address: str
    geom: str
    captureTime: datetime.datetime
    is_pickup: bool
    pickupAt: Optional[datetime.datetime]  # Allowing None for pickupAt
    is_pickup_by_user: Optional[str]  # Allowing None for is_pickup_by_user
    point: int
    total_sampah: int
    sampah_items: List[OutputSampahItem]
    count_items: List[CountObject]
    image: str


class RawData(BaseModel):
    id: int
    address: str
    geom: str
    image: str
    captureTime: datetime.datetime
    point: int
    total_sampah: int
    sampah_items: List[OutputSampahItem]


class Timeseries(BaseModel):
    start_date: datetime.datetime
    end_date: datetime.datetime


class WasteNotCollected(BaseModel):
    id: int
    is_waste_pile: bool
    address: str
    geom: str
    captureTime: datetime.datetime
    waste_count: int


class WasteCollected(BaseModel):
    id: int
    is_waste_pile: bool
    address: str
    geom: str
    pickupAt: Optional[datetime.datetime]  # Allowing None for pickupAt
    waste_count: int
    pickup_by_user: str


class StatisticOutput(BaseModel):
    total_waste_not_collected: int
    total_waste_collected: int
    not_collected: List[WasteNotCollected]
    collected: List[WasteCollected]

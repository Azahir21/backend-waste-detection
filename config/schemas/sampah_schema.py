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
    address: str
    geom: str
    image: str
    captureTime: datetime.datetime
    point: int
    total_sampah: int
    sampah_items: List[OutputSampahItem]
    count_items: List[CountObject]


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

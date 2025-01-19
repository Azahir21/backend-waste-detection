# Define the request body structure
from pydantic import BaseModel


class TPS3RRequest(BaseModel):
    dd_propinsi: str
    dd_district: str = ""
    dd_fasilitas: str = "tps3r"
    exclude_fasilitas: str = ""

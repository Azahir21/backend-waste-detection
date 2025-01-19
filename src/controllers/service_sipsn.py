import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException
from config.schemas.sipsn_schema import TPS3RRequest


async def fetch_tps3r_data(request_data: TPS3RRequest):
    url = "https://sipsn.menlhk.go.id/sipsn/public/home/getMarker"
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    form_data = {
        "dd_propinsi": request_data.dd_propinsi,
        "dd_district": request_data.dd_district,
        "dd_fasilitas": request_data.dd_fasilitas,
        "exclude_fasilitas": request_data.exclude_fasilitas,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=form_data, headers=headers)
            response.raise_for_status()

        response_data = response.json()
        markers = response_data.get("markers", [])
        infowin = response_data.get("infowin", [])

        result = []
        for marker, info in zip(markers, infowin):
            soup = BeautifulSoup(info[0], "html.parser")
            address_parts = [line.strip() for line in soup.stripped_strings]
            full_address = " ".join(address_parts).split("Lat:")[0].strip()

            result.append(
                {
                    "name": marker[0],
                    "latitude": marker[1],
                    "longitude": marker[2],
                    "icon_url": marker[3],
                    "facility_type": marker[4],
                    "id": marker[5],
                    "address": full_address,
                }
            )
        return result

    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request error: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code, detail=f"HTTP error: {e.response.text}"
        )

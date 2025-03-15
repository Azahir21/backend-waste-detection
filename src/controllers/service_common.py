import base64
import json
import os
import io
from PIL import Image
from typing_extensions import Annotated
from fastapi import Depends, HTTPException, UploadFile, logger
from fastapi.security import OAuth2PasswordBearer
from src.controllers.auth.controller_auth import AuthController
from src.controllers.auth import service_jwt
from config.schemas.common_schema import TokenData
import datetime

oauth2_scheme_user = OAuth2PasswordBearer(tokenUrl="/api/v1/login", scheme_name="JWT")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme_user)],
    service_jwt: service_jwt.JWTService = Depends(),
):
    return TokenData.parse_obj(service_jwt.decode_access_token(token))


def insert_image_to_local_base64(
    image_data: str, filename: str, folder: str = "default"
):
    try:
        image_data_dict = json.loads(image_data)
        image_data_dict["image_base64"] = image_data_dict["image_base64"].split(",")[1]
        base64_string = image_data_dict["image_base64"]
        decoded_image = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(decoded_image))
        # Convert RGBA to RGB mode for JPEG compatibility
        if image.mode in ("RGBA", "LA"):
            image = image.convert("RGB")
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{filename}.jpg"
        output_path = f"assets/{folder}/{filename}"
        image.save(output_path, "JPEG", quality=85, optimize=True, progressive=True)
        return output_path
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error saving image file")


def insert_image_to_local(file: UploadFile, folder: str = "default"):
    try:
        content = file.file.read()
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        with open(f"assets/{folder}/{filename}", "wb") as f:
            f.write(content)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error saving image file")
    finally:
        file.file.close()
    return filename


def delete_image_from_local(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"detail": "File deleted successfully"}
    except OSError as e:
        logger.error(f"Error deleting image file: {e}")
        raise HTTPException(status_code=500, detail="Error deleting image file")


def get_image_from_image_path(image_path: str) -> str:
    try:
        normalized_path = os.path.normpath(image_path)
        with open(normalized_path, "rb") as image_file:
            image_data = image_file.read()
        base64_encoded_data = base64.b64encode(image_data).decode("utf-8")
        return base64_encoded_data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


def save_image_base64_to_local(
    image_data: str, filename: str, folder: str = "default", quality: int = 85
):
    try:
        decoded_image = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(decoded_image))
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{filename}.jpg"
        output_path = f"assets/{folder}/{filename}"
        image.save(
            output_path, "JPEG", quality=quality, optimize=True, progressive=True
        )
        return output_path
    except Exception as e:
        print(e)
        HTTPException(status_code=500, detail="Error saving image file")

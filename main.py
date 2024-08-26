from typing import Union
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config.database import engine
from src.routers.router_auth import auth_router
from src.routers.router_article import article_router
from src.routers.router_point import point_router
from src.routers.router_sampah_user import sampah_user_router
from src.routers.router_sampah import sampah_router
from config.models import (
    user_model,
    article_model,
    jenis_sampah_model,
    point_model,
    sampah_model,
    sampah_item_model,
)

app = FastAPI(debug=True, swagger_ui_parameters={"deepLinking": False})

user_model.Base.metadata.create_all(bind=engine)
article_model.Base.metadata.create_all(bind=engine)
jenis_sampah_model.Base.metadata.create_all(bind=engine)
point_model.Base.metadata.create_all(bind=engine)
sampah_model.Base.metadata.create_all(bind=engine)
sampah_item_model.Base.metadata.create_all(bind=engine)

app.mount(
    "/garbage-image",
    StaticFiles(directory="assets/garbage_image"),
    name="garbage_image",
)
app.mount(
    "/article-image",
    StaticFiles(directory="assets/article"),
    name="article_image",
)

app.include_router(auth_router)
app.include_router(article_router)
app.include_router(point_router)
app.include_router(sampah_router)
app.include_router(sampah_user_router)

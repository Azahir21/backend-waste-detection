from typing import Union
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config.database import engine
from src.routers.router_auth import auth_router
from src.routers.router_article import article_router
from src.routers.router_point import point_router
from src.routers.router_sampah_user import sampah_user_router
from src.routers.router_sampah import sampah_router
from src.routers.route_stackholder_auth import auth_stackholder_router
from src.routers.route_stackholder_statistic import statistic_stackholder_router
from src.routers.route_stackholder_sampah import sampah_stackholder_router
from src.routers.route_sipsn_tps import sipsn_tps_router
from config.models import (
    badge_model,
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
badge_model.Base.metadata.create_all(bind=engine)
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
app.mount(
    "/data",
    StaticFiles(directory="assets/data"),
    name="data",
)
app.mount(
    "/evidence",
    StaticFiles(directory="assets/pickup_image"),
    name="evidence",
)

app.include_router(auth_router)
app.include_router(article_router)
app.include_router(point_router)
app.include_router(sampah_router)
app.include_router(sampah_user_router)
app.include_router(auth_stackholder_router)
app.include_router(statistic_stackholder_router)
app.include_router(sampah_stackholder_router)
app.include_router(sipsn_tps_router)

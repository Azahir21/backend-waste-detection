from typing_extensions import Annotated
from fastapi import APIRouter, Depends, File, UploadFile

from config.schemas.article_schema import InputArticle
from config.schemas.common_schema import StandardResponse, TokenData
from src.controllers.service_common import get_current_user
from src.controllers.article.controller_article import ArticleController


article_router = APIRouter(prefix="/api/v1", tags=["Article"])


@article_router.get("/articles")
async def get_all_articles(
    token: Annotated[TokenData, Depends(get_current_user)],
    article_controller: ArticleController = Depends(),
):
    return article_controller.get_articles()


@article_router.get("/article/{title}")
async def get_article_by_title(
    token: Annotated[TokenData, Depends(get_current_user)],
    title: str,
    article_controller: ArticleController = Depends(),
):
    return article_controller.get_article_by_title(title)


@article_router.post("/article")
async def insert_new_article(
    input_article: InputArticle = Depends(),
    file: UploadFile = File(...),
    article_controller: ArticleController = Depends(),
):
    article_controller.insert_new_article(input_article, file)
    return StandardResponse(detail="Success Create Article")


@article_router.delete("/article/{title}")
async def delete_article_by_title(
    title: str,
    article_controller: ArticleController = Depends(),
):
    article_controller.delete_article(title)
    return StandardResponse(detail="Success Delete Article")

from fastapi import HTTPException
from fastapi.params import Depends
from config.schemas.article_schema import InputArticle
from src.controllers.service_common import (
    get_image_from_image_path,
    insert_image_to_local,
)
from src.controllers.auth.service_jwt import JWTService
from src.repositories.repository_article import ArticleRepository


class ArticleController:
    def __init__(
        self,
        article_repository: ArticleRepository = Depends(),
        jwt_service: JWTService = Depends(),
    ):
        self.article_repository = article_repository
        self.jwt_service = jwt_service

    def get_articles(self):
        data = self.article_repository.get_all_articles()
        for article in data:
            article.image = f"https://jjmbm5rz-8000.asse.devtunnels.ms/article-image/{article.image.split('/')[-1]}"
        return data

    def get_article_by_title(self, article_title: str):
        data = self.article_repository.find_article_by_title(article_title)
        if data is None:
            raise HTTPException(status_code=404, detail="Article not found")
        data.image = get_image_from_image_path(data.image)
        return data

    def insert_new_article(self, input_article: InputArticle, file):
        filename = insert_image_to_local(file, folder="article")
        filename = f"assets/article/{filename}"
        found_duplicate_title = self.article_repository.find_article_by_title(
            input_article.title
        )
        if found_duplicate_title:
            raise HTTPException(status_code=404, detail="Title already exists")
        return self.article_repository.insert_new_article(input_article, filename)

    def delete_article(self, title):
        return self.article_repository.delete_article(title)

from datetime import datetime
from fastapi import Depends, HTTPException
from config.database import get_db
from config.models import article_model
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from config.schemas.article_schema import OutputArticle
from src.controllers.service_common import delete_image_from_local


class ArticleRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    DATABASE_ERROR_MESSAGE = "Database error"

    def insert_new_article(self, input_article: article_model.Article, image_path: str):
        try:
            new_article = article_model.Article(
                **input_article.dict(),
                imagePath=image_path,
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
            )
            self.db.add(new_article)
            self.db.commit()
            self.db.refresh(new_article)
            return new_article
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    def get_all_articles(self, page: int, page_size: int):
        try:
            data = self.db.query(article_model.Article)
            total_count = data.count()
            data = data.limit(page_size).offset((page - 1) * page_size).all()
            article_output = []
            for article in data:
                article_output.append(
                    OutputArticle(
                        title=article.title,
                        content=article.content,
                        image=article.imagePath,
                        createdAt=article.createdAt,
                    )
                )
            return article_output, total_count
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    def find_article_by_title(self, title: str):
        try:
            data = (
                self.db.query(article_model.Article)
                .filter(article_model.Article.title == title)
                .first()
            )
            if data is None:
                return None
            data = OutputArticle(
                title=data.title,
                content=data.content,
                image=data.imagePath,
                createdAt=data.createdAt,
            )
            return data
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

    def delete_article(self, title: str):
        try:
            article = (
                self.db.query(article_model.Article)
                .filter(article_model.Article.title == title)
                .first()
            )
            if article is None:
                raise HTTPException(status_code=404, detail="Article not found")
            delete_image_from_local(article.imagePath)
            self.db.delete(article)
            self.db.commit()
            return article
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail=self.DATABASE_ERROR_MESSAGE)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Article
from app.schemas import Article as ArticleSchema, ArticleCreate, ArticleUpdate

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("", response_model=List[ArticleSchema])
def get_articles(
    skip: int = 0,
    limit: int = 100,
    rule_id: int = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Article)
    if rule_id:
        query = query.filter(Article.rule_id == rule_id)
    if status:
        query = query.filter(Article.status == status)
    articles = query.order_by(Article.created_at.desc()).offset(skip).limit(limit).all()
    return articles


@router.get("/{article_id}", response_model=ArticleSchema)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.get("/{article_id}/markdown")
def get_article_markdown(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not article.markdown_file:
        return {"content": ""}
    try:
        with open(article.markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content}
    except FileNotFoundError:
        return {"content": ""}


@router.delete("/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    db.commit()
    return {"message": "Article deleted"}

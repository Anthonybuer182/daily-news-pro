from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from app.models import Article
from app.schemas import ArticleCreate, ArticleUpdate, Article as ArticleSchema
from pydantic import BaseModel


class BatchDeleteRequest(BaseModel):
    ids: List[int]

router = APIRouter(prefix="/api/articles", tags=["articles"])


@router.get("", response_model=List[ArticleSchema])
def get_articles(
    skip: int = 0,
    limit: int = 100,
    rule_id: int = None,
    status: str = None,
    keyword: str = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Article).options(joinedload(Article.rule))
    if rule_id:
        query = query.filter(Article.rule_id == rule_id)
    if status:
        query = query.filter(Article.status == status)
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            (Article.title.ilike(keyword_pattern)) |
            (Article.summary.ilike(keyword_pattern))
        )
    if start_date:
        query = query.filter(Article.created_at >= start_date)
    if end_date:
        query = query.filter(Article.created_at <= end_date)

    total = query.count()
    articles = query.order_by(Article.created_at.desc()).offset(skip).limit(limit).all()

    # Add rule_render and rule_name to each article
    for article in articles:
        if article.rule:
            article.rule_render = article.rule.render
            article.rule_name = article.rule.name

    from app.schemas import Article as ArticleSchema
    articles_data = [ArticleSchema.model_validate(article).model_dump(mode='json') for article in articles]
    response = JSONResponse(content=articles_data)
    response.headers["X-Total-Count"] = str(total)
    return response


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
    import os
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    # 删除关联的 markdown 文件
    if article.markdown_file and os.path.exists(article.markdown_file):
        try:
            os.remove(article.markdown_file)
        except Exception:
            pass
    db.delete(article)
    db.commit()
    return {"message": "Article deleted"}


@router.post("/batch-delete")
def batch_delete_articles(request: BatchDeleteRequest, db: Session = Depends(get_db)):
    """批量删除文章"""
    import os
    deleted_count = 0
    for article_id in request.ids:
        article = db.query(Article).filter(Article.id == article_id).first()
        if article:
            # 删除关联的 markdown 文件
            if article.markdown_file and os.path.exists(article.markdown_file):
                try:
                    os.remove(article.markdown_file)
                except Exception:
                    pass
            db.delete(article)
            deleted_count += 1
    db.commit()
    return {"message": f"Deleted {deleted_count} articles", "deleted_count": deleted_count}

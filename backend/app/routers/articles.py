import json
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from app.models import Article, Rule
from app.schemas import ArticleCreate, ArticleUpdate, Article as ArticleSchema
from pydantic import BaseModel


class BatchDeleteRequest(BaseModel):
    ids: List[int]

router = APIRouter(prefix="/api/articles", tags=["articles"])

# Markdown files should be stored within this directory
MARKDOWN_BASE_DIR = "data/articles"


def is_path_safe(markdown_file: str) -> bool:
    """Validate that the markdown file path is within the expected directory."""
    if not markdown_file:
        return False
    # Resolve the full path and check if it's within MARKDOWN_BASE_DIR
    abs_path = os.path.abspath(markdown_file)
    abs_base = os.path.abspath(MARKDOWN_BASE_DIR)
    return abs_path.startswith(abs_base + os.sep) or abs_path == abs_base


@router.get("", response_model=List[ArticleSchema])
def get_articles(
    skip: int = 0,
    limit: int = 20,
    rule_id: int = None,
    status: str = None,
    keyword: str = None,
    start_date: str = None,
    end_date: str = None,
    source: str = None,      # 新增：来源名称筛选
    time_range: str = None,  # 新增：today, week, month
    tags: str = None,        # 新增：逗号分隔的标签列表
    db: Session = Depends(get_db)
):
    from datetime import datetime, timedelta, timezone
    query = db.query(Article).options(joinedload(Article.rule))

    # 原有筛选
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

    # 来源筛选（通过 rule.name）
    if source:
        query = query.join(Article.rule).filter(Rule.name == source)

    # 时间范围筛选
    if time_range:
        now = datetime.now(timezone.utc)
        if time_range == 'today':
            query = query.filter(Article.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0))
        elif time_range == 'week':
            query = query.filter(Article.created_at >= now - timedelta(days=7))
        elif time_range == 'month':
            query = query.filter(Article.created_at >= now - timedelta(days=30))

    # 标签筛选
    if tags:
        for tag in tags.split(','):
            query = query.filter(Article.tags.ilike(f'%"{tag.strip()}"%'))

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


@router.put("/{article_id}", response_model=ArticleSchema)
def update_article(article_id: int, article_update: ArticleUpdate, db: Session = Depends(get_db)):
    """更新文章"""
    import os
    import json
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    update_data = article_update.model_dump(exclude_unset=True)

    # 处理 tags 字段（从 List 转为 JSON 字符串存储）
    if 'tags' in update_data:
        update_data['tags'] = json.dumps(update_data['tags'], ensure_ascii=False)

    # 如果提供了 markdown_content，更新 markdown 文件
    if 'markdown_content' in update_data:
        content = update_data.pop('markdown_content')
        if article.markdown_file:
            # Validate path to prevent path traversal attacks
            if not is_path_safe(article.markdown_file):
                raise HTTPException(status_code=400, detail="Invalid markdown file path")
            try:
                with open(article.markdown_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to write markdown file: {str(e)}")

    # 更新其他字段
    for field, value in update_data.items():
        setattr(article, field, value)

    db.commit()
    db.refresh(article)
    return article


@router.get("/{article_id}/markdown")
def get_article_markdown(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not article.markdown_file:
        return {"content": ""}
    # Validate path to prevent path traversal attacks
    if not is_path_safe(article.markdown_file):
        raise HTTPException(status_code=400, detail="Invalid markdown file path")
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
    if article.markdown_file:
        # Validate path to prevent path traversal attacks
        if is_path_safe(article.markdown_file) and os.path.exists(article.markdown_file):
            try:
                os.remove(article.markdown_file)
            except Exception:
                pass
    db.delete(article)
    db.commit()
    return {"message": "Article deleted"}


@router.post("/batch-delete")
def batch_delete_articles(ids: List[int] = Body(...), db: Session = Depends(get_db)):
    """批量删除文章"""
    import os
    deleted_count = 0
    for article_id in request.ids:
        article = db.query(Article).filter(Article.id == article_id).first()
        if article:
            # 删除关联的 markdown 文件
            if article.markdown_file:
                # Validate path to prevent path traversal attacks
                if is_path_safe(article.markdown_file) and os.path.exists(article.markdown_file):
                    try:
                        os.remove(article.markdown_file)
                    except Exception:
                        pass
            db.delete(article)
            deleted_count += 1
    db.commit()
    return {"message": f"Deleted {deleted_count} articles", "deleted_count": deleted_count}

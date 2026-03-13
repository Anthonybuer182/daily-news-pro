from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from app.database import get_db
from app.services.analyzer import PageAnalyzer
from app.services.crawler import CrawlerEngine
from app.models import Job

router = APIRouter(prefix="/api", tags=["preview"])


class AnalyzeRequest(BaseModel):
    url: str
    analyze_type: str = "detail"


class PreviewRequest(BaseModel):
    url: str
    rule_id: Optional[int] = None


@router.post("/rules/analyze")
async def analyze_page(request: AnalyzeRequest, db: Session = Depends(get_db)):
    """Analyze page structure"""
    analyzer = PageAnalyzer()
    try:
        result = await analyzer.analyze(request.url, request.analyze_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview")
async def preview_crawl(request: PreviewRequest, db: Session = Depends(get_db)):
    """Preview crawl result"""
    # Create a temporary job
    job = Job(
        rule_id=request.rule_id or 1,
        trigger_type="manual",
        status="pending"
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        engine = CrawlerEngine(db, job.id)
        article = await engine._extract_single_article(request.url)
        if article:
            return {
                "title": article.title,
                "author": article.author,
                "publish_time": article.publish_time,
                "summary": article.summary,
                "cover_image": article.cover_image,
                "markdown": article.markdown_file,
            }
        raise HTTPException(status_code=404, detail="Failed to extract article")
    finally:
        db.delete(job)
        db.commit()

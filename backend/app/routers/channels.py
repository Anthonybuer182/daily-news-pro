from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Channel, ChannelWebhook, Article
from app.schemas import (
    Channel as ChannelSchema,
    ChannelCreate,
    ChannelUpdate,
    ChannelWebhook as ChannelWebhookSchema,
    ChannelWebhookCreate
)
from app.services.http_sender import HttpSender
from datetime import datetime, timezone


router = APIRouter(prefix="/api/channels", tags=["channels"])


@router.get("", response_model=List[ChannelSchema])
def get_channels(db: Session = Depends(get_db)):
    """获取所有渠道列表"""
    channels = db.query(Channel).all()
    return channels


@router.get("/{channel_id}", response_model=ChannelSchema)
def get_channel(channel_id: int, db: Session = Depends(get_db)):
    """获取单个渠道详情"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.post("", response_model=ChannelSchema)
def create_channel(channel_data: ChannelCreate, db: Session = Depends(get_db)):
    """创建新渠道"""
    channel = Channel(
        name=channel_data.name,
        channel_type=channel_data.channel_type,
        push_on_crawl=channel_data.push_on_crawl,
        push_on_schedule=channel_data.push_on_schedule,
        schedule_time=channel_data.schedule_time,
        status=channel_data.status,
        http_method=channel_data.http_method,
        request_headers=channel_data.request_headers,
        message_template=channel_data.message_template
    )
    db.add(channel)
    db.flush()

    for webhook_data in channel_data.webhooks:
        webhook = ChannelWebhook(
            channel_id=channel.id,
            webhook_url=webhook_data.webhook_url,
            is_enabled=webhook_data.is_enabled
        )
        db.add(webhook)

    db.commit()
    db.refresh(channel)
    return channel


@router.put("/{channel_id}", response_model=ChannelSchema)
def update_channel(channel_id: int, channel_data: ChannelUpdate, db: Session = Depends(get_db)):
    """更新渠道配置"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    if channel_data.name is not None:
        channel.name = channel_data.name
    if channel_data.push_on_crawl is not None:
        channel.push_on_crawl = channel_data.push_on_crawl
    if channel_data.push_on_schedule is not None:
        channel.push_on_schedule = channel_data.push_on_schedule
    if channel_data.schedule_time is not None:
        channel.schedule_time = channel_data.schedule_time
    if channel_data.status is not None:
        channel.status = channel_data.status
    if channel_data.http_method is not None:
        channel.http_method = channel_data.http_method
    if channel_data.request_headers is not None:
        channel.request_headers = channel_data.request_headers
    if channel_data.message_template is not None:
        channel.message_template = channel_data.message_template

    channel.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(channel)
    return channel


@router.delete("/{channel_id}")
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    """删除渠道"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    db.delete(channel)
    db.commit()
    return {"message": "Channel deleted"}


@router.post("/{channel_id}/webhooks", response_model=ChannelWebhookSchema)
def add_webhook(channel_id: int, webhook_data: ChannelWebhookCreate, db: Session = Depends(get_db)):
    """添加 Webhook 到渠道"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    webhook = ChannelWebhook(
        channel_id=channel_id,
        webhook_url=webhook_data.webhook_url,
        is_enabled=webhook_data.is_enabled
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return webhook


@router.delete("/{channel_id}/webhooks/{webhook_id}")
def delete_webhook(channel_id: int, webhook_id: int, db: Session = Depends(get_db)):
    """删除渠道的 Webhook"""
    webhook = db.query(ChannelWebhook).filter(
        ChannelWebhook.id == webhook_id,
        ChannelWebhook.channel_id == channel_id
    ).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    db.delete(webhook)
    db.commit()
    return {"message": "Webhook deleted"}


@router.post("/{channel_id}/test")
def test_channel(channel_id: int, db: Session = Depends(get_db)):
    """测试渠道推送"""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    enabled_webhooks = [w.webhook_url for w in channel.webhooks if w.is_enabled]
    if not enabled_webhooks:
        return {"success": False, "message": "没有启用的 Webhook"}

    result = HttpSender.send_test_message(
        webhook_url=enabled_webhooks[0],
        http_method=channel.http_method or "POST",
        request_headers=channel.request_headers,
        message_template=channel.message_template,
        channel_type=channel.channel_type or "http_webhook"
    )
    return {"success": result, "message": "测试消息发送成功" if result else "测试消息发送失败"}


@router.post("/send-now")
def send_now(db: Session = Depends(get_db)):
    """手动触发立即推送"""
    channels = db.query(Channel).filter(
        Channel.status == "enabled",
        Channel.push_on_crawl == True
    ).all()

    if not channels:
        return {"success": False, "message": "没有启用实时推送的渠道"}

    # 获取当天的文章
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    articles = db.query(Article).filter(
        Article.status == "success",
        Article.created_at >= start_of_day
    ).all()

    results = []
    for channel in channels:
        enabled_webhooks = [w.webhook_url for w in channel.webhooks if w.is_enabled]
        if not enabled_webhooks:
            continue

        articles_data = []
        for article in articles:
            articles_data.append({
                "title": article.title or "",
                "summary": article.summary or "",
                "rule_name": article.rule.name if article.rule else "未知来源",
                "publish_time": article.publish_time,
                "url": article.url or ""
            })

        result = HttpSender.send_news(
            webhook_urls=enabled_webhooks,
            articles=articles_data,
            http_method=channel.http_method or "POST",
            request_headers=channel.request_headers,
            message_template=channel.message_template,
            channel_type=channel.channel_type or "http_webhook"
        )
        results.append({
            "channel_id": channel.id,
            "channel_name": channel.name,
            "result": result
        })

    return {
        "success": True,
        "channels_count": len(results),
        "results": results
    }


@router.post("/send-scheduled")
def send_scheduled(db: Session = Depends(get_db)):
    """定时推送接口（由调度器调用）"""
    now = datetime.now()
    channels = db.query(Channel).filter(
        Channel.status == "enabled",
        Channel.push_on_schedule == True
    ).all()

    if not channels:
        return {"success": False, "message": "没有启用定时推送的渠道"}

    # 按时间分组渠道
    channels_by_time = {}
    for channel in channels:
        schedule_time = channel.schedule_time or "09:00"
        if schedule_time not in channels_by_time:
            channels_by_time[schedule_time] = []
        channels_by_time[schedule_time].append(channel)

    # 检查当前时间是否匹配
    current_time = now.strftime("%H:%M")
    matched_channels = channels_by_time.get(current_time, [])

    if not matched_channels:
        return {"success": False, "message": f"当前时间 {current_time} 没有需要推送的渠道"}

    # 获取当天的文章
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    articles = db.query(Article).filter(
        Article.status == "success",
        Article.created_at >= start_of_day
    ).all()

    results = []
    for channel in matched_channels:
        enabled_webhooks = [w.webhook_url for w in channel.webhooks if w.is_enabled]
        if not enabled_webhooks:
            continue

        articles_data = []
        for article in articles:
            articles_data.append({
                "title": article.title or "",
                "summary": article.summary or "",
                "rule_name": article.rule.name if article.rule else "未知来源",
                "publish_time": article.publish_time,
                "url": article.url or ""
            })

        result = HttpSender.send_news(
            webhook_urls=enabled_webhooks,
            articles=articles_data,
            http_method=channel.http_method or "POST",
            request_headers=channel.request_headers,
            message_template=channel.message_template,
            channel_type=channel.channel_type or "http_webhook"
        )
        results.append({
            "channel_id": channel.id,
            "channel_name": channel.name,
            "result": result
        })

    return {
        "success": True,
        "channels_count": len(results),
        "results": results
    }
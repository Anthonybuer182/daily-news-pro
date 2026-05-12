from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import rules, articles, jobs, preview, debug, channels, logs, model_configs, tags
from app.routers import auth
from app.middleware.auth import AdminAuthMiddleware
from app.services.scheduler import CrawlScheduler

app = FastAPI(title="Daily News Pro", description="新闻抓取工具")

# Initialize scheduler
scheduler = CrawlScheduler()

# CORS（限定只允许前端域名，生产环境请改为具体域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin API 鉴权中间件（在 CORS 之后注册，使 CORS 预检请求可以正常通过）
app.add_middleware(AdminAuthMiddleware)

# Initialize database
init_db()

# Include routers
app.include_router(auth.router)
app.include_router(rules.router)
app.include_router(articles.router)
app.include_router(jobs.router)
app.include_router(preview.router)
app.include_router(debug.router)
app.include_router(channels.router)
app.include_router(logs.router)
app.include_router(model_configs.router)
app.include_router(tags.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    scheduler.start()


@app.on_event("shutdown")
async def shutdown():
    scheduler.stop()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)

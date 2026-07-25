import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
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


# ===== 前端静态文件托管（生产环境单进程部署）=====
# 当 STATIC_DIR 指向的前端 dist 目录存在时，由 FastAPI 直接托管，
# 这样服务器无需 Node.js / nginx，也无需在服务器上跑 Vite 构建（2G 内存会 OOM）。
# 注意：此 catch-all 路由在所有 include_router 之后注册，不会拦截 /api/*。
_STATIC_DIR = settings.static_dir
if _STATIC_DIR and os.path.isdir(_STATIC_DIR):
    _ASSETS_DIR = os.path.join(_STATIC_DIR, "assets")
    if os.path.isdir(_ASSETS_DIR):
        app.mount("/assets", StaticFiles(directory=_ASSETS_DIR), name="assets")

    _INDEX_HTML = os.path.join(_STATIC_DIR, "index.html")

    @app.get("/{full_path:path}")
    async def _spa_fallback(full_path: str):
        # 未注册的 /api 路径返回 JSON 404，避免被 SPA 误吞
        if full_path.startswith("api"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        # 根目录静态文件（favicon.ico、vite.svg 等）
        candidate = os.path.join(_STATIC_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        # SPA 路由 fallback 到 index.html
        if os.path.isfile(_INDEX_HTML):
            return FileResponse(_INDEX_HTML)
        return JSONResponse(status_code=404, content={"detail": "Not Found"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)

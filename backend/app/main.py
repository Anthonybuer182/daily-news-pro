from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import rules, articles, jobs, preview, debug, channels
from app.services.scheduler import CrawlScheduler

app = FastAPI(title="Daily News Pro", description="新闻抓取工具")

# Initialize scheduler
scheduler = CrawlScheduler()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Include routers
app.include_router(rules.router)
app.include_router(articles.router)
app.include_router(jobs.router)
app.include_router(preview.router)
app.include_router(debug.router)
app.include_router(channels.router)


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

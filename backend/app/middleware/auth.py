from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.routers.auth import verify_token

# 完全公开的路径前缀（所有方法均放行）
PUBLIC_PREFIXES = (
    "/api/auth",
    "/api/preview",
    "/api/health",
    "/docs",
    "/openapi.json",
    "/redoc",
)

# 仅 GET 方法公开的路径前缀（供预览页面读取展示数据）
PUBLIC_GET_PREFIXES = (
    "/api/articles",
    "/api/tags",
    "/api/rules",
)


class AdminAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 完全公开路径直接放行
        if any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        # 只保护 /api/* 路径
        if not path.startswith("/api/"):
            return await call_next(request)

        # GET 请求的只读展示接口放行
        if request.method == "GET" and any(path.startswith(p) for p in PUBLIC_GET_PREFIXES):
            return await call_next(request)

        # 从 Authorization: Bearer <token> 或 query param ?token= 中取 token
        token = ""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        if not token:
            token = request.query_params.get("token", "")

        if not token or not verify_token(token):
            return JSONResponse(
                status_code=401,
                content={"detail": "未授权，请先登录"},
            )

        return await call_next(request)

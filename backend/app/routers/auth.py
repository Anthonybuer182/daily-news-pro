import hmac
import hashlib
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _make_token(password: str) -> str:
    """用 HMAC-SHA256 生成一个与密码绑定的 token，不依赖额外库。"""
    msg = f"{password}:{settings.secret_key}".encode()
    return hmac.new(settings.secret_key.encode(), msg, hashlib.sha256).hexdigest()


def verify_token(token: str) -> bool:
    expected = _make_token(settings.admin_password)
    return hmac.compare_digest(token, expected)


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    if not hmac.compare_digest(body.password, settings.admin_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码错误",
        )
    token = _make_token(settings.admin_password)
    return LoginResponse(token=token)


@router.get("/verify")
def verify(token: str = ""):
    if not verify_token(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 无效")
    return {"valid": True}

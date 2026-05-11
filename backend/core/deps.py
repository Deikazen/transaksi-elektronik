"""
core/deps.py
FastAPI dependencies untuk autentikasi & otorisasi RBAC.
Dipake sebagai Depends() di semua endpoint yang butuh proteksi.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from database import get_db
from models import User, RoleEnum
from core.security import decode_token

# Skema bearer token (baca dari header Authorization: Bearer <token>)
bearer_scheme = HTTPBearer(auto_error=False)

# ── Ambil user dari token ─────────────────────────────────────
def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials if credentials else request.query_params.get("token")
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kadaluarsa.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise exc
    
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise exc
        user_id: int = payload.get("sub")
        if user_id is None:
            raise exc
    except JWTError:
        raise exc

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise exc
    return user

# ── Cek role (RBAC) ──────────────────────────────────────────
def require_role(*roles: RoleEnum):
    """
    Pake begini di endpoint:
        @router.get("/admin-only")
        def endpoint(user = Depends(require_role(RoleEnum.admin))):
    """
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Role '{current_user.role}' tidak punya izin untuk resource ini.",
            )
        return current_user
    return checker

# Shortcut dependencies yang sering dipake
require_admin   = require_role(RoleEnum.admin)
require_kasir   = require_role(RoleEnum.admin, RoleEnum.kasir)
require_manajer = require_role(RoleEnum.admin, RoleEnum.manajer)
require_any     = require_role(RoleEnum.admin, RoleEnum.kasir, RoleEnum.manajer)
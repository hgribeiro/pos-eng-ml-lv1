from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from fastapi.security import HTTPAuthorizationCredentials

from tc_01.core.security import (
    DEMO_USER,
    create_access_token,
    create_refresh_token,
    decode_token,
    security,
    ACCESS_TOKEN_EXPIRE_MIN,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MIN * 60  # segundos

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MIN * 60

@router.post("/login", response_model=TokenPair)
def auth_login(body: LoginRequest):
    # Validação simplificada: substitua por consulta a BD/LDAP + hash de senha
    if body.username != DEMO_USER["username"] or body.password != DEMO_USER["password"]:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    access = create_access_token(body.username, DEMO_USER["roles"])
    refresh = create_refresh_token(body.username)
    return TokenPair(access_token=access, refresh_token=refresh)

@router.post("/refresh", response_model=AccessTokenResponse)
def auth_refresh(cred: HTTPAuthorizationCredentials = Depends(security)):
    refresh_token = cred.credentials
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Use um refresh token válido")
    username = payload.get("sub")
    access = create_access_token(username, DEMO_USER["roles"])
    return AccessTokenResponse(access_token=access)


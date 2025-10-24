from __future__ import annotations
import os
import jwt
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ===== Config =====
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")   # em prod: variável de ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MIN", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Autenticação via header Authorization: Bearer <token>
security = HTTPBearer(auto_error=True)

# Usuário demo (trocar por BD/LDAP e senhas com hash em produção)
DEMO_USER = {"username": "admin", "password": "admin123", "roles": ["admin"]}

def _create_token(sub: str, token_type: str, expires_delta: timedelta, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    now = datetime.utcnow()
    payload: Dict[str, Any] = {
        "sub": sub,
        "type": token_type,  # "access" | "refresh"
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(username: str, roles: Optional[List[str]] = None) -> str:
    claims = {"roles": roles or []}
    return _create_token(username, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN), claims)

def create_refresh_token(username: str) -> str:
    return _create_token(username, "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_iat": False})
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError as e:
        # DEBUG: expõe causa; remova em produção se não quiser detalhar
        raise HTTPException(status_code=401, detail=f"Token inválido: {e.__class__.__name__}")


def auth_required(cred: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dep de segurança para rotas protegidas por access token.
    - Lê Authorization: Bearer <token>
    - Valida assinatura/expiração e 'type' == 'access'
    - Retorna os 'claims' (sub, roles, etc.)
    """
    token = cred.credentials
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Use um access token válido")
    return payload

def role_required(*required_roles: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Factory de dependência: verifica se o usuário (claims) possui ao menos uma das roles exigidas.
    Uso: def rota(user=Depends(role_required("admin"))): ...
    """
    def _dep(user_claims: Dict[str, Any] = Depends(auth_required)) -> Dict[str, Any]:
        roles = set(user_claims.get("roles", []))
        if not roles.intersection(required_roles):
            raise HTTPException(status_code=403, detail="Acesso negado (permissões insuficientes)")
        return user_claims
    return _dep


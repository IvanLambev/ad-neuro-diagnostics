from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str


@lru_cache
def _build_jwk_client(jwks_url: str):
    return jwt.PyJWKClient(jwks_url)


def _development_user(
    dev_user_id: str | None,
    credentials: HTTPAuthorizationCredentials | None,
) -> AuthenticatedUser:
    if dev_user_id:
        return AuthenticatedUser(user_id=dev_user_id)
    if credentials and credentials.credentials:
        return AuthenticatedUser(user_id=credentials.credentials)
    return AuthenticatedUser(user_id="local-dev-user")


def _clerk_user(
    settings: Settings,
    credentials: HTTPAuthorizationCredentials | None,
) -> AuthenticatedUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    if not settings.clerk_jwks_url or not settings.clerk_issuer:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Clerk auth is not configured")

    token = credentials.credentials
    signing_key = _build_jwk_client(settings.clerk_jwks_url).get_signing_key_from_jwt(token).key
    decode_kwargs = {
        "algorithms": ["RS256"],
        "issuer": settings.clerk_issuer,
        "leeway": settings.clerk_jwt_leeway_sec,
    }
    if settings.clerk_audience:
        decode_kwargs["audience"] = settings.clerk_audience
    payload = jwt.decode(token, signing_key, **decode_kwargs)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")
    return AuthenticatedUser(user_id=user_id)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    dev_user_id: str | None = Header(default=None, alias="X-Dev-User-Id"),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    if settings.auth_mode == "development":
        return _development_user(dev_user_id, credentials)
    if settings.auth_mode == "clerk":
        return _clerk_user(settings, credentials)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unsupported auth mode")

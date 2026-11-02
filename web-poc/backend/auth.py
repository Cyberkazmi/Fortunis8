from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Protocol

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str | None = None
    role: str = "authenticated"


class TokenVerifier(Protocol):
    def verify(self, token: str) -> AuthenticatedUser: ...


class UnconfiguredTokenVerifier:
    def verify(self, token: str) -> AuthenticatedUser:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured for this environment.",
        )


class SupabaseJWTVerifier:
    """Verify Supabase access tokens; never trust an unsigned decoded payload."""

    def __init__(
        self,
        secret: str,
        issuer: str | None = None,
        audience: str | None = "authenticated",
        algorithms: tuple[str, ...] = ("HS256",),
    ) -> None:
        if not secret:
            raise ValueError("A JWT verification secret is required")
        self.secret = secret
        self.issuer = issuer
        self.audience = audience
        self.algorithms = algorithms

    def verify(self, token: str) -> AuthenticatedUser:
        try:
            claims = jwt.decode(
                token,
                self.secret,
                algorithms=list(self.algorithms),
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["sub", "exp", "iat", "aud"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        user_id = claims.get("sub")
        if not isinstance(user_id, str) or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token has no valid user identity.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return AuthenticatedUser(
            user_id=user_id,
            email=claims.get("email") if isinstance(claims.get("email"), str) else None,
            role=claims.get("role", "authenticated"),
        )


def build_token_verifier() -> TokenVerifier:
    secret = os.getenv("SUPABASE_JWT_SECRET")
    if not secret:
        return UnconfiguredTokenVerifier()
    issuer = os.getenv("SUPABASE_JWT_ISSUER") or None
    audience = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
    algorithms = tuple(
        item.strip() for item in os.getenv("SUPABASE_JWT_ALGORITHMS", "HS256").split(",") if item.strip()
    )
    return SupabaseJWTVerifier(secret, issuer=issuer, audience=audience, algorithms=algorithms)


# FastAPI dependency. Tests replace `token_verifier` with a deterministic verifier.
token_verifier: TokenVerifier = build_token_verifier()
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials.strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_verifier.verify(token)

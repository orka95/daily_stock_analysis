# -*- coding: utf-8 -*-
"""
Auth middleware: protect /api/v1/* when admin auth is enabled.
"""

from __future__ import annotations

import logging

from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import JSONResponse

from src.auth import COOKIE_NAME, is_auth_enabled, verify_session

logger = logging.getLogger(__name__)

EXEMPT_PATHS = frozenset({
    "/api/v1/auth/login",
    "/api/v1/auth/status",
    "/api/v1/auth/logout",
    "/api/health",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
})


def _path_exempt(path: str) -> bool:
    """Check if path is exempt from auth."""
    normalized = path.rstrip("/") or "/"
    return normalized in EXEMPT_PATHS


class AuthMiddleware:
    """Require valid session for /api/v1/* when auth is enabled."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if not is_auth_enabled():
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if _path_exempt(path) or not path.startswith("/api/v1/"):
            await self.app(scope, receive, send)
            return

        # Check cookie from headers
        headers = dict(scope.get("headers", []))
        cookie_header = headers.get(b"cookie", b"").decode("latin-1")
        cookie_val = None
        for part in cookie_header.split(";"):
            part = part.strip()
            if part.startswith(COOKIE_NAME + "="):
                cookie_val = part[len(COOKIE_NAME) + 1:]
                break

        if not cookie_val or not verify_session(cookie_val):
            response = JSONResponse(
                status_code=401,
                content={"error": "unauthorized", "message": "Login required"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def add_auth_middleware(app):
    """Add auth middleware to protect API routes."""
    app.add_middleware(AuthMiddleware)

from __future__ import annotations

from app.services.user_service import build_application as _build_user_application


def build_application():
    return _build_user_application()

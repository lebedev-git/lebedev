"""Простейшая аутентификация админа: подписанная сессионная кука."""
import hmac
import time

from fastapi import Request
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, URLSafeSerializer

from .config import ADMIN_PASSWORD, SECRET_KEY

COOKIE_NAME = "lebedev_admin"
_serializer = URLSafeSerializer(SECRET_KEY, salt="admin-session")

# ── Rate-limit логина (in-memory, по IP) ──────────────────────────────────────
_MAX_FAILS = 5           # неудач подряд до блокировки
_LOCK_SECONDS = 300      # блокировка на 5 минут
_attempts: dict[str, tuple[int, float]] = {}  # ip -> (fails, lock_until)


def login_locked(ip: str) -> float:
    """Остаток блокировки в секундах (0 — не заблокирован)."""
    _, lock_until = _attempts.get(ip, (0, 0.0))
    remaining = lock_until - time.monotonic()
    return remaining if remaining > 0 else 0.0


def register_login_result(ip: str, ok: bool) -> None:
    if ok:
        _attempts.pop(ip, None)
        return
    fails = _attempts.get(ip, (0, 0.0))[0] + 1
    lock_until = time.monotonic() + _LOCK_SECONDS if fails >= _MAX_FAILS else 0.0
    _attempts[ip] = (fails, lock_until)


def make_session_token() -> str:
    return _serializer.dumps({"admin": True})


def is_authenticated(request: Request) -> bool:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return False
    try:
        data = _serializer.loads(token)
    except BadSignature:
        return False
    return bool(data.get("admin"))


def check_password(password: str) -> bool:
    # Constant-time сравнение — защита от тайминг-атаки.
    return bool(password) and hmac.compare_digest(password, ADMIN_PASSWORD)


def require_admin(request: Request) -> RedirectResponse | None:
    """Возвращает redirect на логин, если не авторизован, иначе None."""
    if not is_authenticated(request):
        return RedirectResponse("/admin/login", status_code=303)
    return None

"""Точка входа для Phusion Passenger (reg.ru / ISPmanager).

Passenger умеет запускать только WSGI-приложения, а FastAPI — это ASGI.
Мостик через a2wsgi превращает ASGI-приложение в WSGI.

Важно №1: Passenger стартует этот файл тем интерпретатором, который выбран
в панели (может быть системный python). Наши зависимости лежат в venv, поэтому
первым делом перезапускаем сам себя под python из venv (приём из документации
reg.ru). Код до перезапуска намеренно простой и совместим с python 2.7.

Важно №2: a2wsgi НЕ вызывает ASGI-события lifespan (startup/shutdown),
поэтому инициализацию БД и первичный сид запускаем здесь явно.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Переключение на интерпретатор из venv ---------------------------------
INTERP = os.path.join(BASE_DIR, "venv", "bin", "python")
if sys.executable != INTERP and os.path.exists(INTERP):
    os.execl(INTERP, INTERP, *sys.argv)
# Ниже код выполняется уже под python из venv (со всеми зависимостями).

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import db  # noqa: E402
from app.main import app as _asgi_app  # noqa: E402
from app.seed import run as run_seed  # noqa: E402

# Явная инициализация (замена @app.on_event("startup"), который под WSGI не сработает).
db.init_db()
run_seed()

from a2wsgi import ASGIMiddleware  # noqa: E402

# Passenger ищет в этом модуле переменную `application`.
application = ASGIMiddleware(_asgi_app)

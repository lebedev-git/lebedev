"""Точка входа для Phusion Passenger (reg.ru / ISPmanager).

Passenger умеет запускать только WSGI-приложения, а FastAPI — это ASGI.
Мостик через a2wsgi превращает ASGI-приложение в WSGI.

Важно: a2wsgi НЕ вызывает ASGI-события lifespan (startup/shutdown),
поэтому инициализацию БД и первичный сид запускаем здесь явно.
"""
import os
import sys

# Каталог с этим файлом — корень приложения. Добавляем в путь импорта,
# чтобы работал `import app` независимо от рабочей директории Passenger.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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

"""Конфигурация приложения: пути и настройки из окружения."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

APP_DIR = BASE_DIR / "app"
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
DB_PATH = BASE_DIR / "data.db"

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
# Абсолютный адрес сайта для og:image и sitemap. Пусто — берётся из запроса.
SITE_URL = os.getenv("SITE_URL", "").rstrip("/")
# Номер счётчика Яндекс Метрики. Пусто — счётчик не подключается (локально и в тестах).
# Только цифры: значение подставляется в JS, мусор из окружения туда попасть не должен.
_metrika = os.getenv("METRIKA_ID", "").strip()
METRIKA_ID = _metrika if _metrika.isdigit() else ""

# Fail-fast: не стартуем с пустыми/дефолтными секретами.
# Для осознанного локального запуска без .env — ALLOW_INSECURE=1.
_INSECURE = {"", "change-me-please", "replace-with-a-long-random-string", "dev-insecure-secret"}
if os.getenv("ALLOW_INSECURE") != "1":
    _bad = [n for n, v in (("ADMIN_PASSWORD", ADMIN_PASSWORD), ("SECRET_KEY", SECRET_KEY)) if v in _INSECURE]
    if _bad:
        raise RuntimeError(
            f"Небезопасные/пустые секреты: {', '.join(_bad)}. "
            "Задай их в .env (см. .env.example) или запусти с ALLOW_INSECURE=1 для локальной отладки."
        )

# Проекты с закрытым доступом: на карточке красный статус и нет кнопки «Перейти».
PRIVATE_PROJECTS = {"x7-invest"}
# Проекты в разработке: жёлтый статус, кнопки «Перейти» тоже нет.
DEV_PROJECTS = {"english-path"}

# Максимальный размер загружаемого файла (байт)
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 МБ

# Данные владельца портфолио (используются в шаблонах и seed)
OWNER = {
    "name": "Андрей Лебедев",
    "role": "AI Automation Engineer · руководитель проектов",
    "city": "Москва",
    "telegram": "lebedev_core",
    "telegram_url": "https://t.me/lebedev_core",
    "phone": "+7 950 816-39-41",
    "phone_href": "+79508163941",
}

# гарантируем, что папка загрузок существует
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

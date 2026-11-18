"""Статичная копия публичной части сайта для GitHub Pages.

Запуск из корня проекта:
    ALLOW_INSECURE=1 python tools/export_static.py out /lebedev https://lebedev-git.github.io/lebedev

Аргументы: папка вывода, префикс пути (пусто для корня домена), адрес сайта для og и sitemap.
Админки в копии нет: только публичные страницы, static и PDF.
"""
import os
import re
import shutil
import sys
from pathlib import Path

OUT, PREFIX, SITE = Path(sys.argv[1]), sys.argv[2].rstrip("/"), sys.argv[3].rstrip("/")
os.environ["SITE_URL"] = SITE
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio  # noqa: E402

from app import db  # noqa: E402
from app.config import STATIC_DIR  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import run as run_seed  # noqa: E402


class Resp:
    def __init__(self, status_code, text):
        self.status_code, self.text = status_code, text


def get(path: str) -> Resp:
    """Минимальный GET к ASGI-приложению без httpx (TestClient его требует)."""
    scope = {"type": "http", "http_version": "1.1", "method": "GET", "scheme": "https",
             "path": path, "raw_path": path.encode(), "query_string": b"", "root_path": "",
             "headers": [(b"host", b"localhost")], "server": ("localhost", 443), "client": ("127.0.0.1", 1)}
    out = {"status": 0, "body": b""}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        if msg["type"] == "http.response.start":
            out["status"] = msg["status"]
        elif msg["type"] == "http.response.body":
            out["body"] += msg.get("body", b"")

    asyncio.run(app(scope, receive, send))
    return Resp(out["status"], out["body"].decode("utf-8"))


def fix(text: str) -> str:
    # Корневые ссылки "/..." получают префикс репозитория; "//host" и полные URL не трогаем.
    return re.sub(r'(href|src|action|poster)="/(?!/)', rf'\1="{PREFIX}/', text).replace("url(/static", f"url({PREFIX}/static")


if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
db.init_db()
run_seed()
pages = ["/", "/about", "/experience", "/blog"] + [f"/blog/{p['slug']}" for p in db.list_posts() if p["published"]]
for path in pages:
    r = get(path)
    assert r.status_code == 200, (path, r.status_code)
    dst = OUT / path.strip("/") / "index.html"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(fix(r.text), encoding="utf-8")
(OUT / "404.html").write_text(fix(get("/__missing__").text), encoding="utf-8")
(OUT / "sitemap.xml").write_text(get("/sitemap.xml").text, encoding="utf-8")
(OUT / "robots.txt").write_text(get("/robots.txt").text, encoding="utf-8")

shutil.copytree(STATIC_DIR, OUT / "static", ignore=shutil.ignore_patterns(".gitkeep"))
for css in (OUT / "static" / "css").glob("*.css"):
    css.write_text(fix(css.read_text(encoding="utf-8")), encoding="utf-8")
shutil.copy(STATIC_DIR / "favicon.ico", OUT / "favicon.ico")
(OUT / ".nojekyll").write_text("")
print("pages:", len(pages), "->", OUT)

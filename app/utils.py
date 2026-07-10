"""Вспомогательные функции: слаги, сохранение загруженных файлов."""
import re
import unicodedata
from pathlib import Path

from fastapi import UploadFile

from .config import UPLOADS_DIR, MAX_UPLOAD_BYTES

_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

# .svg исключён намеренно: SVG может нести исполняемый скрипт (хранимый XSS).
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = "".join(_TRANSLIT.get(ch, ch) for ch in text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "item"


def unique_slug(base: str, exists) -> str:
    """exists(slug) -> bool. Добавляет суффикс при коллизии."""
    slug = slugify(base)
    candidate = slug
    i = 2
    while exists(candidate):
        candidate = f"{slug}-{i}"
        i += 1
    return candidate


async def save_upload(file: UploadFile | None) -> str:
    """Сохраняет изображение в static/uploads, возвращает имя файла (или '')."""
    if not file or not file.filename:
        return ""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        return ""
    # Читаем максимум MAX+1 байт: ограничивает потребление памяти и режет большие файлы.
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        return ""
    safe_stem = slugify(Path(file.filename).stem)[:40] or "img"
    name = f"{safe_stem}-{_short_id()}{ext}"
    dest = UPLOADS_DIR / name
    dest.write_bytes(content)
    return name


def _short_id() -> str:
    import secrets
    return secrets.token_hex(4)

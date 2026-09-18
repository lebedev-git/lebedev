"""Официальные SVG-иконки стека технологий для прямого инлайнинга в Jinja-шаблоны."""
from __future__ import annotations

import re
from pathlib import Path

ICONS_DIR = Path(__file__).resolve().parent / "static" / "icons"
_CACHE: dict[str, str] = {}


def get_icon_svg(name: str, size: int = 22, extra_class: str = "") -> str:
    """Возвращает оптимизированный inline SVG с заданным размером и fill='currentColor'."""
    key = f"{name}:{size}:{extra_class}"
    if key in _CACHE:
        return _CACHE[key]

    file_path = ICONS_DIR / f"{name}.svg"
    if not file_path.exists():
        return ""

    content = file_path.read_text(encoding="utf-8").strip()

    # Заменяем фиксированные width/height или добавляем их
    content = re.sub(r'\s*(width|height)="[^"]*"', "", content)
    content = re.sub(
        r"<svg\b([^>]*)>",
        rf'<svg\1 width="{size}" height="{size}" class="{extra_class}" fill="currentColor" aria-hidden="true">',
        content,
        count=1,
    )

    # Удаляем title для чистоты DOM
    content = re.sub(r"<title>.*?</title>", "", content)

    _CACHE[key] = content
    return content

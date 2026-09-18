"""Генератор премиальных UI-мокапов обложек для проектов в стиле современных tech-продуктов."""
from __future__ import annotations

import hashlib
from xml.sax.saxutils import escape

TINTS: dict[str, str] = {
    "AI-продукты": "#D0FF7E",
    "Автоматизация": "#59D6C0",
    "Telegram-боты": "#6C8CFF",
    "Дашборды": "#FF7E95",
    "Веб": "#B06CFF",
}
TINT_FALLBACK = "#59D6C0"


def _digits(seed: str) -> list[int]:
    raw = hashlib.sha1(seed.encode("utf-8")).digest()
    return list(raw) * 4


def _tint(category: str) -> str:
    for k, v in TINTS.items():
        if k.lower() in category.lower():
            return v
    return TINT_FALLBACK


def _ai_scene(slug: str, tint: str, w: int, h: int, d: list[int]) -> str:
    """Визуал AI: нейросетевые узлы, векторные связи, агентные модули."""
    return f"""
    <!-- Градиентное свечение -->
    <radialGradient id="glow-{slug}" cx="50%" cy="45%" r="50%">
      <stop offset="0%" stop-color="{tint}" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="{tint}" stop-opacity="0"/>
    </radialGradient>
    <rect x="36" y="36" width="{w-72}" height="{h-72}" rx="12" fill="url(#glow-{slug})"/>

    <!-- Центральный модуль агента -->
    <rect x="220" y="145" width="200" height="90" rx="10" fill="#181B26" stroke="{tint}" stroke-width="1.5" stroke-opacity="0.8"/>
    <text x="320" y="185" text-anchor="middle" fill="#FFFFFF" font-family="'JetBrains Mono', monospace" font-size="13" font-weight="600" letter-spacing="0.05em">AI MODEL / ENGINE</text>
    <text x="320" y="208" text-anchor="middle" fill="{tint}" font-family="'JetBrains Mono', monospace" font-size="11" opacity="0.85">embedding: 1536 dim</text>

    <!-- Левые входные узлы -->
    <g>
      <rect x="68" y="115" width="110" height="42" rx="7" fill="#141722" stroke="rgba(255,255,255,0.1)"/>
      <circle cx="86" cy="136" r="4" fill="{tint}"/>
      <text x="98" y="140" fill="rgba(255,255,255,0.75)" font-family="'JetBrains Mono', monospace" font-size="11">User Prompt</text>
      <path d="M 178 136 C 199 136, 199 175, 220 175" fill="none" stroke="{tint}" stroke-width="1.5" stroke-opacity="0.6"/>

      <rect x="68" y="175" width="110" height="42" rx="7" fill="#141722" stroke="rgba(255,255,255,0.1)"/>
      <circle cx="86" cy="196" r="4" fill="#6C8CFF"/>
      <text x="98" y="200" fill="rgba(255,255,255,0.75)" font-family="'JetBrains Mono', monospace" font-size="11">Context / RAG</text>
      <path d="M 178 196 C 199 196, 199 190, 220 190" fill="none" stroke="{tint}" stroke-width="1.5" stroke-opacity="0.6"/>

      <rect x="68" y="235" width="110" height="42" rx="7" fill="#141722" stroke="rgba(255,255,255,0.1)"/>
      <circle cx="86" cy="256" r="4" fill="#B06CFF"/>
      <text x="98" y="260" fill="rgba(255,255,255,0.75)" font-family="'JetBrains Mono', monospace" font-size="11">Tool Calling</text>
      <path d="M 178 256 C 199 256, 199 205, 220 205" fill="none" stroke="{tint}" stroke-width="1.5" stroke-opacity="0.6"/>
    </g>

    <!-- Правые выходные узлы -->
    <g>
      <path d="M 420 190 C 441 190, 441 155, 462 155" fill="none" stroke="{tint}" stroke-width="1.5" stroke-opacity="0.6"/>
      <rect x="462" y="135" width="115" height="42" rx="7" fill="#141722" stroke="rgba(255,255,255,0.1)"/>
      <text x="478" y="160" fill="{tint}" font-family="'JetBrains Mono', monospace" font-size="11">✓ Structured JSON</text>

      <path d="M 420 190 C 441 190, 441 225, 462 225" fill="none" stroke="{tint}" stroke-width="1.5" stroke-opacity="0.6"/>
      <rect x="462" y="205" width="115" height="42" rx="7" fill="#141722" stroke="rgba(255,255,255,0.1)"/>
      <text x="478" y="230" fill="rgba(255,255,255,0.75)" font-family="'JetBrains Mono', monospace" font-size="11">Stream 68 tok/s</text>
    </g>
    """


def _auto_scene(slug: str, tint: str, w: int, h: int, d: list[int]) -> str:
    """Визуал автоматизации: сценарии n8n, конвейерные узлы, триггеры."""
    return f"""
    <radialGradient id="glow-{slug}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{tint}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{tint}" stop-opacity="0"/>
    </radialGradient>
    <rect x="36" y="36" width="{w-72}" height="{h-72}" rx="12" fill="url(#glow-{slug})"/>

    <!-- Сетка соединений n8n -->
    <path d="M 155 190 L 255 190 M 365 190 L 465 190" stroke="{tint}" stroke-width="2" stroke-dasharray="4 4" stroke-opacity="0.7"/>

    <!-- Узел 1: Webhook -->
    <rect x="65" y="150" width="105" height="80" rx="9" fill="#171A25" stroke="rgba(255,255,255,0.14)"/>
    <circle cx="85" cy="172" r="5" fill="#FFC6DA"/>
    <text x="98" y="176" fill="#FFFFFF" font-family="'JetBrains Mono', monospace" font-size="11" font-weight="600">Webhook</text>
    <text x="75" y="210" fill="rgba(255,255,255,0.5)" font-family="'JetBrains Mono', monospace" font-size="9">POST /event</text>

    <!-- Узел 2: Обработка / LLM -->
    <rect x="255" y="135" width="125" height="110" rx="9" fill="#181B28" stroke="{tint}" stroke-width="1.6"/>
    <circle cx="278" cy="162" r="6" fill="{tint}"/>
    <text x="292" y="166" fill="#FFFFFF" font-family="'JetBrains Mono', monospace" font-size="11" font-weight="600">Pipeline</text>
    <text x="272" y="195" fill="rgba(255,255,255,0.6)" font-family="'JetBrains Mono', monospace" font-size="10">Auto-Parser</text>
    <rect x="272" y="208" width="80" height="18" rx="4" fill="rgba(89,214,192,0.15)"/>
    <text x="278" y="221" fill="{tint}" font-family="'JetBrains Mono', monospace" font-size="9">✓ Success 200</text>

    <!-- Узел 3: Экспорт / База -->
    <rect x="465" y="150" width="115" height="80" rx="9" fill="#171A25" stroke="rgba(255,255,255,0.14)"/>
    <circle cx="485" cy="172" r="5" fill="#D0FF7E"/>
    <text x="498" y="176" fill="#FFFFFF" font-family="'JetBrains Mono', monospace" font-size="11" font-weight="600">Database</text>
    <text x="485" y="210" fill="rgba(255,255,255,0.5)" font-family="'JetBrains Mono', monospace" font-size="9">Synced real-time</text>
    """


def _bot_scene(slug: str, tint: str, w: int, h: int, d: list[int]) -> str:
    """Визуал Telegram-ботов: интерфейс чата, карточка бронирования, команды."""
    return f"""
    <radialGradient id="glow-{slug}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{tint}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{tint}" stop-opacity="0"/>
    </radialGradient>
    <rect x="36" y="36" width="{w-72}" height="{h-72}" rx="12" fill="url(#glow-{slug})"/>

    <!-- Сообщение пользователя -->
    <rect x="340" y="100" width="220" height="42" rx="12" fill="#2B3654"/>
    <text x="355" y="126" fill="#FFFFFF" font-family="'Onest', sans-serif" font-size="12">Забронировать на 19:00</text>

    <!-- Ответ бота -->
    <g>
      <circle cx="85" cy="175" r="14" fill="{tint}"/>
      <text x="85" y="179" text-anchor="middle" fill="#0D1017" font-family="'JetBrains Mono', monospace" font-weight="700" font-size="10">BOT</text>

      <rect x="110" y="155" width="310" height="80" rx="14" fill="#181B26" stroke="rgba(255,255,255,0.1)"/>
      <text x="126" y="182" fill="#FFFFFF" font-family="'Onest', sans-serif" font-size="13" font-weight="500">Бронь подтверждена!</text>
      <text x="126" y="202" fill="rgba(255,255,255,0.6)" font-family="'Onest', sans-serif" font-size="11">Слот: 19:00 — 21:00 · Зал VIP-1</text>
      <text x="126" y="222" fill="{tint}" font-family="'JetBrains Mono', monospace" font-size="10">Код доступа: #849-AK</text>
    </g>

    <!-- Инлайн-кнопки бота -->
    <g>
      <rect x="110" y="245" width="145" height="34" rx="8" fill="rgba(108,140,255,0.2)" stroke="{tint}" stroke-width="1"/>
      <text x="182" y="267" text-anchor="middle" fill="{tint}" font-family="'Onest', sans-serif" font-size="11" font-weight="600">Мой баланс</text>

      <rect x="265" y="245" width="155" height="34" rx="8" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.12)"/>
      <text x="342" y="267" text-anchor="middle" fill="rgba(255,255,255,0.85)" font-family="'Onest', sans-serif" font-size="11">Продлить время</text>
    </g>
    """


def _dash_scene(slug: str, tint: str, w: int, h: int, d: list[int]) -> str:
    """Визуал дашбордов: карточки метрик, плавная линия тренда, аналитика."""
    return f"""
    <radialGradient id="glow-{slug}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{tint}" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="{tint}" stop-opacity="0"/>
    </radialGradient>
    <rect x="36" y="36" width="{w-72}" height="{h-72}" rx="12" fill="url(#glow-{slug})"/>

    <!-- Верхние KPI-карточки -->
    <g>
      <rect x="70" y="95" width="150" height="60" rx="8" fill="#171A24" stroke="rgba(255,255,255,0.08)"/>
      <text x="85" y="118" fill="rgba(255,255,255,0.5)" font-family="'JetBrains Mono', monospace" font-size="10">XIRR / Yield</text>
      <text x="85" y="142" fill="{tint}" font-family="'JetBrains Mono', monospace" font-size="18" font-weight="700">+34.8%</text>

      <rect x="240" y="95" width="150" height="60" rx="8" fill="#171A24" stroke="rgba(255,255,255,0.08)"/>
      <text x="255" y="118" fill="rgba(255,255,255,0.5)" font-family="'JetBrains Mono', monospace" font-size="10">Portfolio MOIC</text>
      <text x="255" y="142" fill="#FFFFFF" font-family="'JetBrains Mono', monospace" font-size="18" font-weight="700">2.4x</text>

      <rect x="410" y="95" width="160" height="60" rx="8" fill="#171A24" stroke="rgba(255,255,255,0.08)"/>
      <text x="425" y="118" fill="rgba(255,255,255,0.5)" font-family="'JetBrains Mono', monospace" font-size="10">Processed Leads</text>
      <text x="425" y="142" fill="#59D6C0" font-family="'JetBrains Mono', monospace" font-size="18" font-weight="700">14,290</text>
    </g>

    <!-- Сетка графика -->
    <line x1="70" y1="210" x2="570" y2="210" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3 3"/>
    <line x1="70" y1="260" x2="570" y2="260" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3 3"/>

    <!-- Градиентная заливка под графиком -->
    <linearGradient id="chartGrad-{slug}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{tint}" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="{tint}" stop-opacity="0.0"/>
    </linearGradient>
    <path d="M 70 270 Q 140 250, 200 220 T 320 195 T 440 170 T 570 145 L 570 295 L 70 295 Z" fill="url(#chartGrad-{slug})"/>
    <path d="M 70 270 Q 140 250, 200 220 T 320 195 T 440 170 T 570 145" fill="none" stroke="{tint}" stroke-width="2.5" stroke-linecap="round"/>

    <!-- Активная точка на графике -->
    <circle cx="440" cy="170" r="5" fill="#FFFFFF" stroke="{tint}" stroke-width="2"/>
    <circle cx="570" cy="145" r="5" fill="#FFFFFF" stroke="{tint}" stroke-width="2"/>
    """


def _web_scene(slug: str, tint: str, w: int, h: int, d: list[int]) -> str:
    """Визуал веб-сервисов: интерфейс платформы, модули, структура."""
    return f"""
    <radialGradient id="glow-{slug}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{tint}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{tint}" stop-opacity="0"/>
    </radialGradient>
    <rect x="36" y="36" width="{w-72}" height="{h-72}" rx="12" fill="url(#glow-{slug})"/>

    <!-- Левый сайдбар -->
    <rect x="65" y="95" width="105" height="195" rx="8" fill="#141620" stroke="rgba(255,255,255,0.07)"/>
    <rect x="80" y="115" width="75" height="12" rx="4" fill="{tint}" opacity="0.8"/>
    <rect x="80" y="140" width="65" height="10" rx="3" fill="rgba(255,255,255,0.2)"/>
    <rect x="80" y="160" width="70" height="10" rx="3" fill="rgba(255,255,255,0.2)"/>
    <rect x="80" y="180" width="55" height="10" rx="3" fill="rgba(255,255,255,0.2)"/>

    <!-- Основной контент платформы -->
    <rect x="185" y="95" width="385" height="110" rx="8" fill="#181B26" stroke="rgba(255,255,255,0.09)"/>
    <rect x="205" y="115" width="140" height="16" rx="4" fill="#FFFFFF" opacity="0.9"/>
    <rect x="205" y="142" width="280" height="10" rx="3" fill="rgba(255,255,255,0.3)"/>
    <rect x="205" y="160" width="220" height="10" rx="3" fill="rgba(255,255,255,0.3)"/>
    <rect x="205" y="182" width="90" height="14" rx="4" fill="{tint}" opacity="0.2"/>
    <text x="212" y="193" fill="{tint}" font-family="'JetBrains Mono', monospace" font-size="9">Platform UI</text>

    <!-- Нижние виджеты -->
    <rect x="185" y="215" width="185" height="75" rx="8" fill="#151722" stroke="rgba(255,255,255,0.07)"/>
    <circle cx="210" cy="245" r="14" fill="rgba(208,255,126,0.2)"/>
    <text x="235" y="248" fill="#FFFFFF" font-family="'JetBrains Mono', monospace" font-size="11">Gantt Track</text>

    <rect x="380" y="215" width="190" height="75" rx="8" fill="#151722" stroke="rgba(255,255,255,0.07)"/>
    <circle cx="405" cy="245" r="14" fill="rgba(198,186,255,0.2)"/>
    <text x="430" y="248" fill="#FFFFFF" font-family="'JetBrains Mono', monospace" font-size="11">AI Search</text>
    """


def cover_svg(project, width: int = 640, height: int = 400) -> str:
    """Генерирует премиальный UI-мокап окна приложения под проект."""
    def field(name: str, default: str = "") -> str:
        try:
            val = project[name]
        except (KeyError, IndexError, TypeError):
            val = default
        return str(val or default)

    slug = field("slug", "project")
    title = field("title")
    category = field("tags").split(",")[0].strip() if field("tags") else "Проект"

    d = _digits(slug)
    tint = _tint(category)

    # Выбор сцены по категории
    cat_l = category.lower()
    if "ai" in cat_l or "llm" in cat_l:
        scene = _ai_scene(slug, tint, width, height, d)
    elif "автомат" in cat_l or "n8n" in cat_l:
        scene = _auto_scene(slug, tint, width, height, d)
    elif "бот" in cat_l or "telegram" in cat_l:
        scene = _bot_scene(slug, tint, width, height, d)
    elif "дашборд" in cat_l or "аналит" in cat_l:
        scene = _dash_scene(slug, tint, width, height, d)
    else:
        scene = _web_scene(slug, tint, width, height, d)

    pattern_grid = (
        f'<pattern id="dots-{slug}" width="20" height="20" patternUnits="userSpaceOnUse">'
        f'<circle cx="2" cy="2" r="1" fill="#FFFFFF" opacity="0.04"/>'
        f'</pattern>'
    )

    clean_title = escape(title[:30] + ('...' if len(title) > 30 else ''))

    return f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{escape(title)}" preserveAspectRatio="xMidYMid slice">
  <defs>
    {pattern_grid}
    <linearGradient id="bgGrad-{slug}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#141620"/>
      <stop offset="100%" stop-color="#0E1017"/>
    </linearGradient>
  </defs>

  <!-- Внешний холст -->
  <rect width="{width}" height="{height}" rx="22" fill="url(#bgGrad-{slug})"/>
  <rect width="{width}" height="{height}" rx="22" fill="url(#dots-{slug})"/>

  <!-- Верхняя панель окна macOS -->
  <rect x="24" y="24" width="{width-48}" height="38" rx="10" fill="#181B26" stroke="rgba(255,255,255,0.06)"/>
  <circle cx="44" cy="43" r="4.5" fill="#FF5F56" opacity="0.8"/>
  <circle cx="58" cy="43" r="4.5" fill="#FFBD2E" opacity="0.8"/>
  <circle cx="72" cy="43" r="4.5" fill="#27C93F" opacity="0.8"/>
  <text x="{width // 2}" y="47" text-anchor="middle" fill="rgba(255,255,255,0.4)" font-family="'JetBrains Mono', monospace" font-size="11">{clean_title}</text>

  <!-- Тематическая сцена продукта -->
  {scene}

  <!-- Тонкая внутренняя подсветка рамки -->
  <rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="21.5" fill="none" stroke="rgba(255,255,255,0.08)"/>
</svg>"""

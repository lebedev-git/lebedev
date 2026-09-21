"""Работа с SQLite: подключение, схема, вспомогательные запросы."""
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS project (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    slug        TEXT NOT NULL UNIQUE,
    summary     TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    cover_image TEXT NOT NULL DEFAULT '',
    tags        TEXT NOT NULL DEFAULT '',
    role        TEXT NOT NULL DEFAULT '',
    year        TEXT NOT NULL DEFAULT '',
    link        TEXT NOT NULL DEFAULT '',
    featured    INTEGER NOT NULL DEFAULT 0,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS visit (
    day     TEXT NOT NULL,              -- дата визита, YYYY-MM-DD
    visitor TEXT NOT NULL,              -- хэш посетителя; сырой IP не храним
    hits    INTEGER NOT NULL DEFAULT 1, -- просмотров страниц за этот день
    PRIMARY KEY (day, visitor)
);

CREATE TABLE IF NOT EXISTS post (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    slug        TEXT NOT NULL UNIQUE,
    excerpt     TEXT NOT NULL DEFAULT '',
    body        TEXT NOT NULL DEFAULT '',
    cover_image TEXT NOT NULL DEFAULT '',
    published   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_cursor() -> Iterator[sqlite3.Cursor]:
    conn = get_connection()
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Создаёт таблицы, если их ещё нет."""
    with db_cursor() as cur:
        cur.executescript(SCHEMA)


# ── Проекты ────────────────────────────────────────────────────────────────
def list_projects(only_featured: bool = False) -> list[sqlite3.Row]:
    q = "SELECT * FROM project"
    if only_featured:
        q += " WHERE featured = 1"
    q += " ORDER BY sort_order ASC, created_at DESC"
    with db_cursor() as cur:
        return cur.execute(q).fetchall()


def get_project(slug: str) -> sqlite3.Row | None:
    with db_cursor() as cur:
        return cur.execute("SELECT * FROM project WHERE slug = ?", (slug,)).fetchone()


def get_project_by_id(pid: int) -> sqlite3.Row | None:
    with db_cursor() as cur:
        return cur.execute("SELECT * FROM project WHERE id = ?", (pid,)).fetchone()


def create_project(data: dict) -> None:
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO project
               (title, slug, summary, description, cover_image, tags, role, year, link, featured, sort_order)
               VALUES (:title, :slug, :summary, :description, :cover_image, :tags, :role, :year, :link, :featured, :sort_order)""",
            data,
        )


def update_project(pid: int, data: dict) -> None:
    data = {**data, "id": pid}
    with db_cursor() as cur:
        cur.execute(
            """UPDATE project SET
               title=:title, slug=:slug, summary=:summary, description=:description,
               cover_image=:cover_image, tags=:tags, role=:role, year=:year,
               link=:link, featured=:featured, sort_order=:sort_order
               WHERE id=:id""",
            data,
        )


def delete_project(pid: int) -> None:
    with db_cursor() as cur:
        cur.execute("DELETE FROM project WHERE id = ?", (pid,))


# ── Блог ───────────────────────────────────────────────────────────────────
def list_posts(only_published: bool = True) -> list[sqlite3.Row]:
    q = "SELECT * FROM post"
    if only_published:
        q += " WHERE published = 1"
    q += " ORDER BY created_at DESC"
    with db_cursor() as cur:
        return cur.execute(q).fetchall()


def get_post(slug: str) -> sqlite3.Row | None:
    with db_cursor() as cur:
        return cur.execute("SELECT * FROM post WHERE slug = ?", (slug,)).fetchone()


def get_post_by_id(pid: int) -> sqlite3.Row | None:
    with db_cursor() as cur:
        return cur.execute("SELECT * FROM post WHERE id = ?", (pid,)).fetchone()


def create_post(data: dict) -> None:
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO post (title, slug, excerpt, body, cover_image, published)
               VALUES (:title, :slug, :excerpt, :body, :cover_image, :published)""",
            data,
        )


def update_post(pid: int, data: dict) -> None:
    data = {**data, "id": pid}
    with db_cursor() as cur:
        cur.execute(
            """UPDATE post SET
               title=:title, slug=:slug, excerpt=:excerpt, body=:body,
               cover_image=:cover_image, published=:published
               WHERE id=:id""",
            data,
        )


def delete_post(pid: int) -> None:
    with db_cursor() as cur:
        cur.execute("DELETE FROM post WHERE id = ?", (pid,))


def count_rows() -> tuple[int, int]:
    with db_cursor() as cur:
        p = cur.execute("SELECT COUNT(*) FROM project").fetchone()[0]
        b = cur.execute("SELECT COUNT(*) FROM post").fetchone()[0]
        return p, b


# ── Посещаемость ───────────────────────────────────────────────────────────
# Свой счётчик вместо внешней аналитики: ни одного запроса на сторону,
# сырых IP в базе нет — только хэш, посчитанный на секрете приложения.
def record_visit(visitor: str) -> None:
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO visit (day, visitor, hits) VALUES (date('now'), ?, 1) "
            "ON CONFLICT(day, visitor) DO UPDATE SET hits = hits + 1",
            (visitor,),
        )


def visit_stats(days: int = 14) -> dict:
    """Сводка для админки: сегодня, за неделю, за всё время и разбивка по дням."""
    with db_cursor() as cur:
        row = cur.execute(
            """SELECT
                 (SELECT COUNT(*) FROM visit WHERE day = date('now'))                       AS today_people,
                 (SELECT IFNULL(SUM(hits), 0) FROM visit WHERE day = date('now'))           AS today_hits,
                 (SELECT COUNT(*) FROM visit WHERE day = date('now', '-1 day'))             AS yesterday_people,
                 (SELECT COUNT(DISTINCT visitor) FROM visit
                    WHERE day >= date('now', '-6 days'))                                    AS week_people,
                 (SELECT COUNT(DISTINCT visitor) FROM visit)                                AS total_people,
                 (SELECT IFNULL(SUM(hits), 0) FROM visit)                                   AS total_hits,
                 (SELECT MIN(day) FROM visit)                                               AS since"""
        ).fetchone()
        rows = cur.execute(
            "SELECT day, COUNT(*) AS people, SUM(hits) AS hits FROM visit "
            "WHERE day >= date('now', ?) GROUP BY day ORDER BY day DESC",
            (f"-{days - 1} days",),
        ).fetchall()
    return {**dict(row), "days": rows}

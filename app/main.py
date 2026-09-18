"""FastAPI-приложение: публичные страницы + лёгкая админка."""
from typing import Annotated

from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db
from .covers import cover_svg
from .icons import get_icon_svg
from .auth import (
    COOKIE_NAME,
    check_password,
    is_authenticated,
    login_locked,
    make_session_token,
    register_login_result,
    require_admin,
)
from .config import OWNER, SITE_URL, STATIC_DIR, TEMPLATES_DIR, UPLOADS_DIR
from .content import ABOUT, EXPERIENCE, SERVICES, SKILLS, STATS
from .seed import run as run_seed
from .utils import save_upload, unique_slug

app = FastAPI(title="Портфолио · Андрей Лебедев")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["owner"] = OWNER
templates.env.globals["cover_svg"] = cover_svg
templates.env.globals["icon_svg"] = get_icon_svg
templates.env.globals["asset_v"] = str(int(__import__("time").time()))  # сброс кэша статики на каждый запуск


def plural(n: int, one: str, few: str, many: str) -> str:
    """2 внедрения, 5 внедрений, 21 внедрение."""
    n = abs(n) % 100
    if 11 <= n <= 19:
        return many
    n %= 10
    return one if n == 1 else few if 2 <= n <= 4 else many


templates.env.globals["plural"] = plural


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return resp


def site_url(request: Request) -> str:
    """Абсолютный адрес сайта для og:image, canonical и sitemap."""
    return SITE_URL or str(request.base_url).rstrip("/")


@app.on_event("startup")
def _startup() -> None:
    db.init_db()
    run_seed()


def render(request: Request, name: str, status_code: int = 200, **ctx) -> HTMLResponse:
    ctx.setdefault("site_url", site_url(request))
    return templates.TemplateResponse(
        request=request, name=name, context=ctx, status_code=status_code
    )


@app.get("/robots.txt", include_in_schema=False)
def robots(request: Request):
    return PlainTextResponse(
        f"User-agent: *\nDisallow: /admin\nSitemap: {site_url(request)}/sitemap.xml\n"
    )


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap(request: Request):
    base = site_url(request)
    paths = ["/", "/about", "/experience", "/blog"] + [f"/blog/{p['slug']}" for p in db.list_posts()]
    urls = "".join(f"<url><loc>{base}{p}</loc></url>" for p in paths)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return Response(xml, media_type="application/xml")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav = STATIC_DIR / "favicon.ico"
    if fav.exists():
        return FileResponse(fav, media_type="image/x-icon")
    return Response(status_code=204)


# ── Публичные страницы ───────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    items = db.list_projects()
    sections = ["AI-продукты", "Автоматизация", "Telegram-боты", "Дашборды", "Веб"]
    tag_counts = {}
    for p in items:
        cat = p["tags"].split(",")[0].strip() if p["tags"] else ""
        if cat:
            tag_counts[cat] = tag_counts.get(cat, 0) + 1
    tags = [s for s in sections if s in tag_counts]
    # Живая обложка: tools/record_cover.py кладёт cover-<slug>.mp4 рядом с картинкой.
    video_covers = {p["slug"] for p in items if (UPLOADS_DIR / f"cover-{p['slug']}.mp4").exists()}
    return render(
        request, "index.html",
        projects=items,
        video_covers=video_covers,
        sections=tags,
        tag_counts=tag_counts,
        about=ABOUT,
    )


@app.get("/projects", response_class=HTMLResponse)
def projects(request: Request):
    return RedirectResponse("/", status_code=303)


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return render(request, "about.html", about=ABOUT)


@app.get("/experience", response_class=HTMLResponse)
def experience(request: Request):
    return render(request, "experience.html", experience=EXPERIENCE, skills=SKILLS, stats=STATS)


@app.get("/blog", response_class=HTMLResponse)
def blog(request: Request):
    return render(request, "blog.html", posts=db.list_posts())


@app.get("/blog/{slug}", response_class=HTMLResponse)
def post_detail(request: Request, slug: str):
    post = db.get_post(slug)
    if not post or not post["published"]:
        return render(request, "404.html", status_code=404)
    return render(request, "post.html", post=post)


# ── Админка: аутентификация ──────────────────────────────────────────────────
@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_form(request: Request):
    if is_authenticated(request):
        return RedirectResponse("/admin", status_code=303)
    return render(request, "admin/login.html", error=None)


@app.post("/admin/login")
def admin_login(request: Request, password: Annotated[str, Form()]):
    ip = request.client.host if request.client else "?"
    locked = login_locked(ip)
    if locked:
        return render(
            request, "admin/login.html",
            error=f"Слишком много попыток. Повторите через {int(locked // 60) + 1} мин.",
            status_code=429,
        )
    if not check_password(password):
        register_login_result(ip, ok=False)
        return render(request, "admin/login.html", error="Неверный пароль", status_code=401)
    register_login_result(ip, ok=True)
    resp = RedirectResponse("/admin", status_code=303)
    resp.set_cookie(
        COOKIE_NAME, make_session_token(),
        httponly=True, samesite="lax", max_age=60 * 60 * 24 * 14,
        secure=request.url.scheme == "https",
    )
    return resp


@app.get("/admin/logout")
def admin_logout():
    resp = RedirectResponse("/admin/login", status_code=303)
    resp.delete_cookie(COOKIE_NAME)
    return resp


# ── Админка: дашборд ─────────────────────────────────────────────────────────
@app.get("/admin", response_class=HTMLResponse)
def admin_home(request: Request):
    if (r := require_admin(request)):
        return r
    return render(
        request, "admin/dashboard.html",
        projects=db.list_projects(), posts=db.list_posts(only_published=False),
    )


# ── Админка: проекты ─────────────────────────────────────────────────────────
@app.get("/admin/projects/new", response_class=HTMLResponse)
def project_new(request: Request):
    if (r := require_admin(request)):
        return r
    return render(request, "admin/project_form.html", p=None, action="/admin/projects/new")


@app.post("/admin/projects/new")
async def project_create(
    request: Request,
    title: Annotated[str, Form()],
    summary: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    tags: Annotated[str, Form()] = "",
    role: Annotated[str, Form()] = "",
    year: Annotated[str, Form()] = "",
    link: Annotated[str, Form()] = "",
    featured: Annotated[str, Form()] = "",
    sort_order: Annotated[str, Form()] = "0",
    cover: UploadFile = File(None),
):
    if (r := require_admin(request)):
        return r
    slug = unique_slug(title, lambda s: db.get_project(s) is not None)
    cover_name = await save_upload(cover)
    db.create_project({
        "title": title, "slug": slug, "summary": summary, "description": description,
        "cover_image": cover_name, "tags": tags, "role": role, "year": year, "link": link,
        "featured": 1 if featured else 0, "sort_order": _to_int(sort_order),
    })
    return RedirectResponse("/admin", status_code=303)


@app.get("/admin/projects/{pid}/edit", response_class=HTMLResponse)
def project_edit(request: Request, pid: int):
    if (r := require_admin(request)):
        return r
    p = db.get_project_by_id(pid)
    if not p:
        return RedirectResponse("/admin", status_code=303)
    return render(request, "admin/project_form.html", p=p, action=f"/admin/projects/{pid}/edit")


@app.post("/admin/projects/{pid}/edit")
async def project_update(
    request: Request,
    pid: int,
    title: Annotated[str, Form()],
    summary: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    tags: Annotated[str, Form()] = "",
    role: Annotated[str, Form()] = "",
    year: Annotated[str, Form()] = "",
    link: Annotated[str, Form()] = "",
    featured: Annotated[str, Form()] = "",
    sort_order: Annotated[str, Form()] = "0",
    cover: UploadFile = File(None),
):
    if (r := require_admin(request)):
        return r
    current = db.get_project_by_id(pid)
    if not current:
        return RedirectResponse("/admin", status_code=303)
    cover_name = await save_upload(cover) or current["cover_image"]
    db.update_project(pid, {
        "title": title, "slug": current["slug"], "summary": summary, "description": description,
        "cover_image": cover_name, "tags": tags, "role": role, "year": year, "link": link,
        "featured": 1 if featured else 0, "sort_order": _to_int(sort_order),
    })
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/projects/{pid}/delete")
def project_remove(request: Request, pid: int):
    if (r := require_admin(request)):
        return r
    db.delete_project(pid)
    return RedirectResponse("/admin", status_code=303)


# ── Админка: блог ────────────────────────────────────────────────────────────
@app.get("/admin/posts/new", response_class=HTMLResponse)
def post_new(request: Request):
    if (r := require_admin(request)):
        return r
    return render(request, "admin/post_form.html", post=None, action="/admin/posts/new")


@app.post("/admin/posts/new")
async def post_create(
    request: Request,
    title: Annotated[str, Form()],
    excerpt: Annotated[str, Form()] = "",
    body: Annotated[str, Form()] = "",
    published: Annotated[str, Form()] = "",
    cover: UploadFile = File(None),
):
    if (r := require_admin(request)):
        return r
    slug = unique_slug(title, lambda s: db.get_post(s) is not None)
    cover_name = await save_upload(cover)
    db.create_post({
        "title": title, "slug": slug, "excerpt": excerpt, "body": body,
        "cover_image": cover_name, "published": 1 if published else 0,
    })
    return RedirectResponse("/admin", status_code=303)


@app.get("/admin/posts/{pid}/edit", response_class=HTMLResponse)
def post_edit(request: Request, pid: int):
    if (r := require_admin(request)):
        return r
    post = db.get_post_by_id(pid)
    if not post:
        return RedirectResponse("/admin", status_code=303)
    return render(request, "admin/post_form.html", post=post, action=f"/admin/posts/{pid}/edit")


@app.post("/admin/posts/{pid}/edit")
async def post_update(
    request: Request,
    pid: int,
    title: Annotated[str, Form()],
    excerpt: Annotated[str, Form()] = "",
    body: Annotated[str, Form()] = "",
    published: Annotated[str, Form()] = "",
    cover: UploadFile = File(None),
):
    if (r := require_admin(request)):
        return r
    current = db.get_post_by_id(pid)
    if not current:
        return RedirectResponse("/admin", status_code=303)
    cover_name = await save_upload(cover) or current["cover_image"]
    db.update_post(pid, {
        "title": title, "slug": current["slug"], "excerpt": excerpt, "body": body,
        "cover_image": cover_name, "published": 1 if published else 0,
    })
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/posts/{pid}/delete")
def post_remove(request: Request, pid: int):
    if (r := require_admin(request)):
        return r
    db.delete_post(pid)
    return RedirectResponse("/admin", status_code=303)


def _to_int(v: str) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0

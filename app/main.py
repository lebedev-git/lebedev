"""FastAPI-приложение: публичные страницы + лёгкая админка."""
from typing import Annotated

from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db
from .auth import (
    COOKIE_NAME,
    check_password,
    is_authenticated,
    login_locked,
    make_session_token,
    register_login_result,
    require_admin,
)
from .config import OWNER, STATIC_DIR, TEMPLATES_DIR
from .content import ABOUT, EXPERIENCE, SKILLS, STATS
from .seed import run as run_seed
from .utils import save_upload, unique_slug

app = FastAPI(title="Портфолио · Андрей Лебедев")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["owner"] = OWNER


@app.on_event("startup")
def _startup() -> None:
    db.init_db()
    run_seed()


def render(request: Request, name: str, status_code: int = 200, **ctx) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name=name, context=ctx, status_code=status_code
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    # Пустой ответ вместо 404 (убирает ошибку в консоли).
    return Response(status_code=204)


# ── Публичные страницы ───────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render(
        request, "index.html",
        featured=db.list_projects(only_featured=True),
        stats=STATS,
        skills=SKILLS,
    )


@app.get("/projects", response_class=HTMLResponse)
def projects(request: Request):
    items = db.list_projects()
    # Фиксированные разделы (первый тег каждой карточки = её раздел)
    sections = ["AI-продукты", "Автоматизация", "Telegram-боты", "Дашборды", "Веб"]
    present = {p["tags"].split(",")[0].strip() for p in items}
    tags = [s for s in sections if s in present]
    return render(request, "projects.html", projects=items, tags=tags)


@app.get("/projects/{slug}", response_class=HTMLResponse)
def project_detail(request: Request, slug: str):
    proj = db.get_project(slug)
    if not proj:
        return render(request, "404.html", status_code=404)
    return render(request, "project.html", p=proj)


@app.get("/scene", response_class=HTMLResponse)
def scene(request: Request):
    """Прототип пространственной сцены: зона проектов на серой коробке."""
    return render(request, "scene.html", projects=db.list_projects())


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

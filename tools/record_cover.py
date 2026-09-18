"""Запись живой обложки проекта: прогон страницы в Chromium с видео.

    python tools/record_cover.py mayak https://rosdk.ru/mayak-guide-3d

Сырой ролик Playwright (.webm) ffmpeg пережимает в
app/static/uploads/cover-<slug>.mp4 — карточка на главной подхватит его сама. Сценарий прогона —
в SCENARIOS: что кликать и куда тянуть мышью, чтобы кадр был живым.
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "app" / "static" / "uploads"
W, H = 1280, 800  # 16:10 — как обложка карточки 640×400


def orbit(page, x0, y0, x1, y1, steps=40, pause=0.02):
    """Плавное перетаскивание мышью: так крутятся 3D-сцены и карусели."""
    page.mouse.move(x0, y0)
    page.mouse.down()
    for i in range(1, steps + 1):
        page.mouse.move(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps)
        time.sleep(pause)
    page.mouse.up()


def mayak(page):
    """Стол мастера: клик по предмету — камера подлетает, Esc — назад."""
    page.wait_for_timeout(9000)                      # предметы раскладываются на стол
    for x, y in ((640, 460), (600, 215), (235, 440), (1045, 460)):
        page.mouse.move(x, y, steps=12)
        page.wait_for_timeout(500)
        page.mouse.click(x, y)
        page.wait_for_timeout(2600)
        page.keyboard.press("Escape")
        page.wait_for_timeout(1600)


def eng(page):
    """English Path: прогулка по разделам — клик по пунктам меню, скролл."""
    page.wait_for_timeout(2500)
    links = page.locator("nav a, header a").filter(has_not_text="")
    hrefs = []
    for i in range(links.count()):
        href = links.nth(i).get_attribute("href") or ""
        if href.startswith("/") and href not in hrefs and href != "/":
            hrefs.append(href)
    for href in hrefs[:4]:
        page.mouse.wheel(0, 500); page.wait_for_timeout(700)
        page.goto(page.url.split("/", 3)[0] + "//" + page.url.split("/", 3)[2] + href, wait_until="networkidle")
        page.wait_for_timeout(1400)
    page.mouse.wheel(0, 700); page.wait_for_timeout(1200)


def x7(page):
    """X7 Invest: закрытое приложение, сессия из .auth. Пройти по вкладкам."""
    page.wait_for_timeout(2500)
    for path in X7_TABS:
        page.goto(page.url.split("/", 3)[0] + "//" + page.url.split("/", 3)[2] + path, wait_until="networkidle")
        page.wait_for_timeout(600)
        page.mouse.wheel(0, 400); page.wait_for_timeout(1400)


X7_TABS = ["/", "/analytics", "/deals"]  # дашборд, графики, карточки сделок; выплаты — таблица, скучно

# Ключ — slug проекта в базе: по нему карточка находит cover-<slug>.mp4.
SCENARIOS = {"mayak": mayak, "english-path": eng, "x7-invest": x7}
KEEP = {"mayak": 19.0, "english-path": 10.0, "x7-invest": 10.0}  # сколько последних секунд оставить


AUTH = ROOT / ".auth"  # сессии закрытых приложений; в .gitignore
GPU_ARGS = ["--use-gl=angle", "--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist"]


def login(slug: str, url: str) -> None:
    """Открыть обычное окно: пользователь входит сам, сессия сохраняется в .auth/<slug>.json.

    Пароль скрипту не нужен и нигде не хранится — только cookies и localStorage
    после входа. Ждём, пока в адресе или хранилище появится признак входа."""
    AUTH.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=GPU_ARGS)
        ctx = browser.new_context(viewport={"width": W, "height": H})
        page = ctx.new_page()
        page.goto(url)
        print("Войди в приложение в открывшемся окне. Жду до 5 минут…", flush=True)
        page.wait_for_function(
            "() => Object.keys(localStorage).some(k => /auth|token|session/i.test(k)) || document.cookie.length > 20",
            timeout=300_000,
        )
        page.wait_for_timeout(1500)
        ctx.storage_state(path=str(AUTH / f"{slug}.json"))
        print("Сессия сохранена:", AUTH / f"{slug}.json")
        browser.close()


def main(slug: str, url: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / ".playwright-mcp" / "video"
    shutil.rmtree(tmp, ignore_errors=True)
    state = AUTH / f"{slug}.json"
    with sync_playwright() as p:
        # GPU обязателен: на SwiftShader сцена рисует ~10 fps, и ролик дёргается.
        browser = p.chromium.launch(args=GPU_ARGS)
        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            record_video_dir=str(tmp),
            record_video_size={"width": W, "height": H},
            device_scale_factor=1,
            storage_state=str(state) if state.exists() else None,
        )
        page = ctx.new_page()
        t0 = time.time()
        page.goto(url, wait_until="networkidle")
        SCENARIOS[slug](page)
        # видео пишется с открытия вкладки: белый экран и загрузку отрезаем
        ss = f"{max(time.time() - t0 - KEEP[slug], 0):.1f}"
        ctx.close()
        browser.close()
    raw = next(tmp.glob("*.webm"))
    mp4 = OUT / f"cover-{slug}.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-ss", ss, "-i", str(raw),
        "-vf", "scale=960:-2,fps=30", "-c:v", "libx264", "-preset", "slow", "-crf", "24",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(mp4),
    ], check=True, capture_output=True)
    print(mp4, mp4.stat().st_size // 1024, "КБ")


if __name__ == "__main__":
    if sys.argv[1] == "login":
        login(sys.argv[2], sys.argv[3])
    else:
        main(sys.argv[1], sys.argv[2])

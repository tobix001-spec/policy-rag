"""Record the README demo: drive the real UI (real API, real models) and build docs/demo/demo.gif.

Prerequisites: API on :8000 and UI on :8501 already running, then
    uv sync --group demo && uv run python -m playwright install chromium
    uv run python scripts/record_demo.py

Every frame is a real screenshot of a live answer; nothing is mocked or edited apart from the caption bar.
"""
from __future__ import annotations

import time
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import Page, sync_playwright

API = "http://127.0.0.1:8000"
UI = "http://127.0.0.1:8501"
OUT = Path(__file__).resolve().parents[1] / "docs" / "demo"
VIEWPORT = {"width": 1440, "height": 1000}
GIF_WIDTH = 1100
FRAME_MS = 3800

SCENES = [  # (file stem, caption, role, question or tab)
    ("01-simple", "1 · Simple lookup: cited source, confidence, latency and cost, on the small 3b model",
     "customer", "What is the maximum file size for uploads in the mobile app?"),
    ("02-comparison", "2 · Comparison: one retrieval per product, both values stated, routed to the 7b model",
     "customer", "Which has the lower collision deductible: Classic Car or Premier Auto?"),
    ("03-unanswerable", "3 · 'Bronze PPO' doesn't exist (only Bronze HMO): the verifier holds the draft for review",
     "customer", "What is the deductible for the Bronze PPO plan?"),
    ("04-access-customer", "4a · Access control: a customer cannot retrieve internal adjuster documents",
     "customer", "What is the large-loss referral threshold for auto claims?"),
    ("05-access-staff", "4b · Same question as staff: the internal guideline is retrieved and cited",
     "staff", "What is the large-loss referral threshold for auto claims?"),
    ("06-cache", "5 · Repeat question: served from the semantic cache, 0 tokens, $0",
     "customer", "What is the maximum file size for uploads in the mobile app?"),
    ("07-review", "6 · Human-in-the-loop: low-confidence and abstained answers wait here for a reviewer",
     None, "Review queue"),
    ("08-eval", "7 · Evaluation: 180-case golden set, regression gate vs the previous version",
     None, "Evaluation"),
]


def wait_ready() -> None:
    for _ in range(120):
        try:
            if httpx.get(f"{API}/health", timeout=3).json().get("status") == "ok" and \
                    httpx.get(UI, timeout=3).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(2)
    raise SystemExit("API/UI not ready on :8000 / :8501")


def settle(page: Page, timeout_s: int = 180) -> None:
    """Wait until Streamlit has finished rerunning (no spinner, no 'running' indicator)."""
    page.wait_for_timeout(600)
    page.wait_for_function(
        "() => !document.body.innerText.includes('Retrieving and generating') && "
        "!document.querySelector('[data-testid=\"stStatusWidget\"] [data-testid=\"stStatusWidgetRunningIcon\"]')",
        timeout=timeout_s * 1000)
    page.wait_for_timeout(1200)


def ask(page: Page, role: str, question: str) -> None:
    sidebar = page.locator('[data-testid="stSidebar"]')
    sidebar.get_by_text(role, exact=True).click()
    settle(page)
    box = page.get_by_label("Question", exact=True)
    box.fill(question)
    box.press("Enter")
    settle(page)
    page.get_by_role("button", name="Ask").click()
    settle(page)
    # open the first *source* expander (its title contains a chunk id like "...#c1"), never the latency one
    # (visible only: Streamlit keeps the previous run's elements, hidden, in the DOM)
    sources = page.locator('[data-testid="stExpander"]').filter(has_text="#c").filter(visible=True)
    if sources.count():
        sources.first.click(timeout=5000)
        page.wait_for_timeout(600)
    page.evaluate("() => { for (const el of [document.querySelector('[data-testid=\"stMain\"]'), "
                  "document.scrollingElement]) { if (el) el.scrollTo(0, 0); } }")
    page.wait_for_timeout(400)


def caption(png: Path, text: str) -> Image.Image:
    img = Image.open(png).convert("RGB")
    img = img.resize((GIF_WIDTH, int(img.height * GIF_WIDTH / img.width)), Image.LANCZOS)
    bar_h = 46
    out = Image.new("RGB", (img.width, img.height + bar_h), (17, 24, 39))
    out.paste(img, (0, bar_h))
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("segoeuib.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    draw.text((16, 12), text, fill=(255, 255, 255), font=font)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wait_ready()
    httpx.post(f"{API}/cache/clear", timeout=10)  # so scene 1 is a real miss and scene 6 a real hit

    shots: list[tuple[Path, str]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)
        page.goto(UI)
        settle(page)
        for stem, text, role, arg in SCENES:
            if role is None:
                page.get_by_role("tab", name=arg).click()
                settle(page)
            else:
                page.get_by_role("tab", name="Ask").click()
                settle(page)
                ask(page, role, arg)
            path = OUT / f"{stem}.png"
            page.screenshot(path=str(path))
            shots.append((path, text))
            print(f"captured {path.name}", flush=True)
        browser.close()

    frames = [caption(path, text) for path, text in shots]
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in frames]
    gif = OUT / "demo.gif"
    pal[0].save(gif, save_all=True, append_images=pal[1:], duration=FRAME_MS, loop=0, optimize=True)
    print(f"wrote {gif} ({gif.stat().st_size / 1e6:.1f} MB, {len(frames)} frames)")


if __name__ == "__main__":
    main()

import asyncio
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

PROFILE_URL = "https://www.instagram.com/devops_cloud_ai_with_sanjeev/"

PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "output"
VIDEO_URLS_FILE = OUTPUT_DIR / "video_urls.txt"
JSON_FILE = OUTPUT_DIR / "instagram_videos.json"
COOKIE_FILE = OUTPUT_DIR / "instagram_cookies.txt"

CHROME_USER_DATA = (
    Path.home() / "AppData" / "Local" / "InstagramCollectorChrome"
)

MAX_SCROLLS = 250
SCROLL_DELAY_MS = 3500
STOP_AFTER_UNCHANGED_ROUNDS = 18
EXPECTED_VIDEO_COUNT = 40


def get_username(profile_url):
    return urlparse(profile_url).path.strip("/").split("/")[0]


def normalize_url(url):
    if not url:
        return None

    url = url.strip().split("?")[0]

    if url.startswith("/"):
        url = "https://www.instagram.com" + url

    if not url.startswith(("https://", "http://")):
        return None

    return url.rstrip("/") + "/"


def parse_post_url(url, username):
    """Accept Instagram Reel, post and TV URL formats."""

    try:
        normalized = normalize_url(url)

        if not normalized:
            return None

        parsed = urlparse(normalized)

        if parsed.netloc.lower() not in (
            "instagram.com",
            "www.instagram.com",
        ):
            return None

        parts = [part for part in parsed.path.split("/") if part]

        if len(parts) == 2 and parts[0].lower() in (
            "reel", "reels", "p", "tv"
        ):
            post_type, shortcode = parts

        elif len(parts) >= 3:
            post_username, post_type, shortcode = parts[:3]

            if post_username.lower() != username.lower():
                return None

        else:
            return None

        if post_type.lower() not in ("reel", "reels", "p", "tv"):
            return None

        if not shortcode:
            return None

        canonical_type = (
            "reel" if post_type.lower() == "reels"
            else post_type.lower()
        )

        return (
            f"https://www.instagram.com/"
            f"{canonical_type}/{shortcode}/"
        )

    except Exception:
        return None


def load_existing_urls(username):
    """Load old and current URL files and remove duplicates."""

    urls = set()

    candidates = [
        VIDEO_URLS_FILE,
        PROJECT_DIR / "video_urls.txt",
    ]

    for path in candidates:
        if not path.exists():
            continue

        try:
            for line in path.read_text(
                encoding="utf-8"
            ).splitlines():

                parsed = parse_post_url(line, username)

                if parsed:
                    urls.add(parsed)

        except OSError as exc:
            print(f"Warning reading {path}: {exc}")

    json_candidates = [
        JSON_FILE,
        PROJECT_DIR / "instagram_videos.json",
    ]

    for path in json_candidates:
        if not path.exists():
            continue

        try:
            data = json.loads(
                path.read_text(encoding="utf-8")
            )

            records = (
                data if isinstance(data, list)
                else data.get("videos", [])
            )

            for item in records:
                if isinstance(item, dict):
                    parsed = parse_post_url(
                        item.get("url", ""),
                        username,
                    )

                    if parsed:
                        urls.add(parsed)

        except (
            OSError,
            json.JSONDecodeError,
            AttributeError,
            TypeError,
        ):
            print(f"Warning reading JSON: {path}")

    return urls


def save_urls(urls, username):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ordered = sorted(urls)

    VIDEO_URLS_FILE.write_text(
        "".join(url + "\n" for url in ordered),
        encoding="utf-8",
    )

    records = []

    for url in ordered:
        parts = [
            part
            for part in urlparse(url).path.split("/")
            if part
        ]

        records.append({
            "url": url,
            "username": username,
            "post_type": parts[0],
            "shortcode": parts[1],
        })

    JSON_FILE.write_text(
        json.dumps(
            records,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


async def extract_post_links(page, username):
    hrefs = await page.locator("a[href]").evaluate_all(
        """
        elements => elements
            .map(element => element.getAttribute('href'))
            .filter(Boolean)
        """
    )

    found = set()

    for href in hrefs:
        parsed = parse_post_url(href, username)

        if parsed:
            found.add(parsed)

    return found


async def reset_browser_zoom(page):
    """
    Automatically reset Chrome zoom to 100%.
    This reproduces the manual Ctrl + 0 action.
    """

    print("\nResetting browser zoom to 100%...")

    await page.bring_to_front()

    try:
        await page.keyboard.press("Control+0")
        await page.wait_for_timeout(2500)

        print("Browser zoom reset command sent.")

    except Exception as exc:
        print(f"Zoom reset warning: {exc}")

    viewport = page.viewport_size

    print(f"Browser viewport: {viewport}")


async def prime_feed_scroll(page):
    """
    Trigger the first real mouse-wheel scroll after page load.
    Instagram may need this interaction before lazy loading starts.
    """

    print("\nPreparing Instagram feed...")

    await page.wait_for_timeout(2000)

    viewport = page.viewport_size or {
        "width": 1400,
        "height": 900,
    }

    center_x = viewport["width"] // 2
    center_y = viewport["height"] // 2

    await page.mouse.move(center_x, center_y)

    # First scroll interaction
    await page.mouse.wheel(0, 900)
    await page.wait_for_timeout(2500)

    # Second scroll interaction
    await page.mouse.wheel(0, 900)
    await page.wait_for_timeout(2500)

    print("Initial feed scroll completed.")


async def scroll_one_step(page):
    """
    Scroll the largest scrollable container and also send
    a real mouse-wheel event.
    """

    state = await page.evaluate(
        """
        () => {
            const doc =
                document.scrollingElement ||
                document.documentElement;

            const all = [
                doc,
                ...Array.from(document.querySelectorAll('body *'))
            ];

            const candidates = all.filter(el => {
                if (!el) return false;

                const style = getComputedStyle(el);

                return (
                    el.scrollHeight - el.clientHeight > 80 &&
                    (
                        el === doc ||
                        style.overflowY === 'auto' ||
                        style.overflowY === 'scroll'
                    )
                );
            });

            candidates.sort((a, b) =>
                (b.scrollHeight - b.clientHeight) -
                (a.scrollHeight - a.clientHeight)
            );

            const target = candidates[0] || doc;

            const before = target.scrollTop;

            const step = Math.max(
                650,
                Math.floor(
                    (target.clientHeight || window.innerHeight) * 0.85
                )
            );

            target.scrollBy({
                top: step,
                left: 0,
                behavior: 'auto'
            });

            window.scrollBy(0, step);

            return {
                tag: target.tagName,

                topBefore: before,
                topAfter: target.scrollTop,

                height: target.scrollHeight,
                client: target.clientHeight,

                pageHeight: doc.scrollHeight,
                pageTop: window.scrollY
            };
        }
        """
    )

    # Real mouse wheel interaction
    await page.mouse.wheel(0, 1100)

    return state


async def scroll_and_collect(page, urls, username):
    idle_rounds = 0
    previous_count = len(urls)
    previous_signature = None

    for number in range(1, MAX_SCROLLS + 1):

        before = len(urls)

        urls.update(
            await extract_post_links(page, username)
        )

        newly_found = len(urls) - before

        state = await scroll_one_step(page)

        # Wait for Instagram lazy loading
        await page.wait_for_timeout(SCROLL_DELAY_MS)

        before_after = len(urls)

        urls.update(
            await extract_post_links(page, username)
        )

        newly_found += len(urls) - before_after

        if newly_found:
            save_urls(urls, username)

        signature = (
            len(urls),
            state["height"],
            state["topAfter"],
            state["pageHeight"],
            state["pageTop"],
        )

        if (
            len(urls) > previous_count
            or signature != previous_signature
        ):
            idle_rounds = 0
        else:
            idle_rounds += 1

        previous_count = len(urls)
        previous_signature = signature

        at_bottom = (
            (
                state["topAfter"] +
                max(state["client"], 1)
            ) >= state["height"] - 15

            or

            (
                state["pageTop"] + 950
            ) >= state["pageHeight"] - 15
        )

        print(
            f"Scroll {number}/{MAX_SCROLLS} | "
            f"+{newly_found} URLs | "
            f"Total {len(urls)} | "
            f"container={state['tag']} | "
            f"top={state['topAfter']} | "
            f"pageTop={state['pageTop']} | "
            f"height={state['height']} | "
            f"pageHeight={state['pageHeight']} | "
            f"idle={idle_rounds}"
        )

        if (
            at_bottom
            and idle_rounds >= STOP_AFTER_UNCHANGED_ROUNDS
        ):
            print(
                "\nNo additional posts loaded after "
                "repeated bottom-of-feed checks."
            )
            break

    return urls


def export_cookies(cookies):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with COOKIE_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        file.write("# Netscape HTTP Cookie File\n")

        for cookie in cookies:
            domain = cookie.get("domain", "")

            expires = int(
                cookie.get("expires", 0) or 0
            )

            file.write(
                f"{domain}\t"
                f"{'TRUE' if domain.startswith('.') else 'FALSE'}\t"
                f"{cookie.get('path', '/')}\t"
                f"{'TRUE' if cookie.get('secure') else 'FALSE'}\t"
                f"{expires}\t"
                f"{cookie.get('name', '')}\t"
                f"{cookie.get('value', '')}\n"
            )


async def run_collector():
    username = get_username(PROFILE_URL)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CHROME_USER_DATA.mkdir(
        parents=True,
        exist_ok=True,
    )

    urls = load_existing_urls(username)

    print(f"\nExisting unique URLs: {len(urls)}")

    async with async_playwright() as playwright:

        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(CHROME_USER_DATA),
            headless=False,
            viewport={
                "width": 1400,
                "height": 900,
            },
            args=[
                "--start-maximized",
            ],
        )

        try:
            page = (
                context.pages[0]
                if context.pages
                else await context.new_page()
            )

            reels_url = (
                PROFILE_URL.rstrip("/") + "/reels/"
            )

            print(
                "\nOpening Instagram Reels tab:",
                reels_url,
            )

            await page.goto(
                reels_url,
                wait_until="domcontentloaded",
                timeout=90000,
            )

            await page.wait_for_timeout(8000)

            if "accounts/login" in page.url:

                print(
                    "\nInstagram login required. "
                    "Please log in manually in Chrome."
                )

                input(
                    "After login and when the profile is visible, "
                    "press ENTER..."
                )

                await page.goto(
                    reels_url,
                    wait_until="domcontentloaded",
                    timeout=90000,
                )

                await page.wait_for_timeout(8000)

            if "instagram.com" not in page.url:
                raise RuntimeError(
                    f"Instagram did not open correctly: {page.url}"
                )

            # NEW: Automatically reset Chrome zoom
            await reset_browser_zoom(page)

            # NEW: Trigger initial feed scrolling
            await prime_feed_scroll(page)

            initial = await extract_post_links(
                page,
                username,
            )

            if not initial:

                print(
                    "Reels tab returned no post links; "
                    "trying profile root."
                )

                await page.goto(
                    PROFILE_URL,
                    wait_until="domcontentloaded",
                    timeout=90000,
                )

                await page.wait_for_timeout(8000)

                # Apply the same zoom and scroll preparation
                await reset_browser_zoom(page)
                await prime_feed_scroll(page)

                initial = await extract_post_links(
                    page,
                    username,
                )

            urls.update(initial)

            save_urls(urls, username)

            print(
                f"\nInitially discovered URLs: {len(initial)}"
            )

            print(
                f"Existing + newly discovered unique URLs: "
                f"{len(urls)}"
            )

            print(
                f"Expected count mentioned: "
                f"{EXPECTED_VIDEO_COUNT}"
            )

            print("\nStarting gradual scrolling...")

            await scroll_and_collect(
                page,
                urls,
                username,
            )

            # Final extraction after scrolling
            urls.update(
                await extract_post_links(
                    page,
                    username,
                )
            )

            save_urls(urls, username)

            export_cookies(
                await context.cookies()
            )

            print("\n====================================")
            print("COLLECTION COMPLETED")
            print("====================================")

            print(
                "Total unique candidate post URLs:",
                len(urls),
            )

            print(
                "URL file:",
                VIDEO_URLS_FILE.resolve(),
            )

            print(
                "JSON file:",
                JSON_FILE.resolve(),
            )

            print(
                "Cookie file:",
                COOKIE_FILE.resolve(),
            )

            if len(urls) < EXPECTED_VIDEO_COUNT:
                print(
                    f"\nNOTE: Found {len(urls)} of "
                    f"{EXPECTED_VIDEO_COUNT} expected items. "
                    "Instagram did not expose more post links "
                    "during this run."
                )

            return sorted(urls)

        finally:
            await context.close()


def collect_video_urls(
    profile_url=None,
    urls_file=None,
    browser=None,
):
    global PROFILE_URL
    global OUTPUT_DIR
    global VIDEO_URLS_FILE
    global JSON_FILE
    global COOKIE_FILE

    if profile_url:
        PROFILE_URL = (
            profile_url.rstrip("/") + "/"
        )

    if urls_file:
        VIDEO_URLS_FILE = Path(urls_file)

        OUTPUT_DIR = VIDEO_URLS_FILE.parent

        JSON_FILE = (
            OUTPUT_DIR / "instagram_videos.json"
        )

        COOKIE_FILE = (
            OUTPUT_DIR / "instagram_cookies.txt"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    return asyncio.run(
        run_collector()
    )


def discover_video_urls(
    profile_url=None,
    urls_file=None,
    browser=None,
):
    return collect_video_urls(
        profile_url,
        urls_file,
        browser,
    )


if __name__ == "__main__":
    collect_video_urls()
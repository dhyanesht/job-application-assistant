import argparse
import asyncio
import logging
import signal
from pathlib import Path
import json

from .browser import create_browser
from .scraper import scrape_pages
from .config import DEFAULT_QUERY_PARAMS
from .logging_config import setup_logging

shutdown_event = asyncio.Event()
PROGRESS_PATH = Path("progress.json")

def setup_signals(logger: logging.Logger) -> None:
    loop = asyncio.get_running_loop()

    def _handle_shutdown() -> None:
        logger.warning("Shutdown signal received. Finishing current tasks...")
        shutdown_event.set()

    try:
        loop.add_signal_handler(signal.SIGINT, _handle_shutdown)
        loop.add_signal_handler(signal.SIGTERM, _handle_shutdown)
    except NotImplementedError:
        # e.g. Windows / some environments
        logger.debug("Signal handlers not supported on this platform.")

def load_resume_metadata():
    if not PROGRESS_PATH.exists():
        return None

    try:
        with PROGRESS_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Corrupt or unreadable; start fresh
        return None


def save_resume_metadata(page_num: int, query: dict) -> None:
    data = {
        "last_completed_page": page_num,
        "query": query,
    }
    with PROGRESS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f)



async def async_main():
    parser = argparse.ArgumentParser(description="Dice Job Scraper (Async Playwright)")
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--with-details", action="store_true")
    parser.add_argument("--jobs-per-page", type=int, default=5)
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from last_completed_page if progress.json exists")

    args = parser.parse_args()

    setup_logging(getattr(logging, args.log_level.upper()))
    logger = logging.getLogger(__name__)

    setup_signals(logger)

    resume_meta = load_resume_metadata() if args.resume else None
    start_page = (resume_meta["last_completed_page"] + 1) if resume_meta else 1

    playwright, browser, context, list_page = await create_browser(
        headless=not args.headed
    )

    detail_page = await context.new_page()

    try:
        jobs, csv_path = await scrape_pages(
            list_page=list_page,
            detail_page=detail_page,
            query_params=DEFAULT_QUERY_PARAMS,
            max_pages=args.pages,
            jobs_per_page=args.jobs_per_page,
            output_dir=args.output_dir,
            start_page=start_page,          # new
            shutdown_event=shutdown_event,  # new
            save_progress=save_resume_metadata,  # callback
        )

        logger.info(
            "Scraping complete",
            extra={
                "total_jobs": len(jobs),
                "csv": str(csv_path),
            },
        )

    finally:
        await context.close()
        await browser.close()
        await playwright.stop()


def main():
    asyncio.run(async_main())

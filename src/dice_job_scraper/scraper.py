# scraper.py
import asyncio
import logging
import time
from urllib.parse import urlencode

from .config import BASE_URL, PAGE_TIMEOUT
from .parser import extract_total_pages, extract_jobs
from .exporter import write_jobs_to_csv, write_jobs_to_jsonl_async
from .job_details import parse_job_page
from .position_type_classifier import extract_position_type

logger = logging.getLogger(__name__)


def build_page_url(query_params: dict, page: int) -> str:
    params = query_params.copy()
    params["page"] = page
    return f"{BASE_URL}?{urlencode(params)}"


async def scrape_job_details(page, job_url: str) -> dict:
    try:
        logger.info(f"Scraping details for page {job_url}")
        await page.goto(job_url, timeout=30000)
        await page.wait_for_selector("h1")

        html = await page.content()
        logger.info("Page Content length %s", len(html))
        return parse_job_page(html)

    except Exception as e:
        logger.warning("Failed to scrape job detail | url=%s | error=%s", job_url, str(e))
        return {}


async def scrape_pages(
        list_page,
        detail_page,
        query_params: dict,
        max_pages: int,
        jobs_per_page: int,
        output_dir: str,
        start_page: int = 1,
        shutdown_event: asyncio.Event | None = None,
        save_progress=None,  # callable: (page_num: int, query: dict) -> None
):
    all_jobs = []
    jsonl_path = await write_jobs_to_jsonl_async(jobs=[], output_dir=output_dir)

    current_page = start_page
    last_page = start_page + max_pages - 1

    while current_page <= last_page:
        # Optional: allow external shutdown
        if shutdown_event is not None and shutdown_event.is_set():
            logger.warning("Shutdown requested. Stopping before page %s", current_page)
            break

        url = build_page_url(query_params, current_page)

        logger.info(
            f"Scraping page {current_page}, {url}")

        await list_page.goto(url, timeout=PAGE_TIMEOUT)
        await list_page.wait_for_selector('div[role="listitem"]')

        html = await list_page.content()

        total_pages = extract_total_pages(html)
        jobs = extract_jobs(html, jobs_per_page)

        logger.info(
            "Page scraped",
            extra={
                "page": current_page,
                "total_pages": total_pages,
                "jobs_scraped": len(jobs),
            },
        )
        detailed_jobs = []

        for job in jobs:
            time.sleep(10)
            if job["url"] != "N/A":
                details = await scrape_job_details(detail_page, job["url"])
                job.update(details)
                # AI classification not needed as we can extract this details from page badges itself.
                # position = extract_position_type(details.get("Job Description"))
                # logger.info(f"Position type {position}")

            detailed_jobs.append(job)

        all_jobs.extend(detailed_jobs)
        jsonl_path = await write_jobs_to_jsonl_async(
            detailed_jobs,
            output_dir,
            append=True,
            jsonl_path=jsonl_path,
        )

        # Persist progress after each successful page
        if save_progress is not None:
            save_progress(current_page, query_params)

        if current_page >= total_pages:
            logger.info("Reached last page")
            break

        current_page += 1

    csv_path = write_jobs_to_csv(all_jobs, output_dir)
    logger.info(
        "All exports complete | csv=%s | jsonl=%s", csv_path, jsonl_path
    )

    return all_jobs, csv_path

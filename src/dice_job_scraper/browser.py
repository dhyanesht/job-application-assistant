from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)

async def create_browser(headless=True):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    context = await browser.new_context()
    page = await context.new_page()
    return playwright, browser, context, page

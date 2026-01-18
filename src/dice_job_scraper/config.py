# src/dice_job_scraper/config.py

BASE_URL = "https://www.dice.com/jobs"

DEFAULT_QUERY_PARAMS = {
    "filters.employmentType": "CONTRACTS|THIRD_PARTY",
    "filters.postedDate": "THREE",
    "q": "Java Developer",
}

PAGE_TIMEOUT = 10_000  # Playwright timeout in ms

from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def extract_total_pages(html: str) -> int:
    soup = BeautifulSoup(html, "lxml")
    section = soup.find("section", {"aria-label": lambda x: x and "Page" in x})
    if not section:
        return 1
    text = section.get_text(strip=True)
    return int(text.split("of")[-1])


def extract_jobs(html: str, limit: int) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    cards = soup.find_all("div", {"role": "listitem"})[:limit]

    jobs = []
    for card in cards:
        title = card.find("a", {"data-testid": "job-search-job-detail-link"})
        company = card.find("p", class_="text-sm")
        location = card.find("p", string=lambda x: x and "," in x)

        jobs.append({
            "title": title.text.strip() if title else "N/A",
            "company": company.text.strip() if company else "N/A",
            "location": location.text.strip() if location else "N/A",
            "url": title["href"] if title else "N/A",
        })

    return jobs
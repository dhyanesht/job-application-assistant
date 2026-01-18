from dice_job_scraper.config import BASE_URL

def test_base_url_exists():
    assert BASE_URL.startswith("https://")

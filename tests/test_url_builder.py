from dice_job_scraper.scraper import build_page_url

def test_build_page_url():
    url = build_page_url({"q": "Java"}, 2)
    assert "page=2" in url

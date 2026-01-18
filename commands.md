
Initializing
```shell
pip install poetry
poetry --version
poetry add playwright beautifulsoup4 lxml
poetry add --group dev pytest black ruff
poetry run playwright install chromium

poetry run dice-scraper --pages 3 --jobs-per-page 2
poetry run pytest

poetry run black src tests
poetry run ruff check src
poetry add aiofiles

```

GITHUB Actions
```yaml
- run: pip install poetry
- run: poetry install
- run: poetry run pytest

```

poetry run dice-scraper --pages 100 --jobs-per-page 100 --output-dir output --log-level INFO
poetry run dice-scraper --pages 2 --jobs-per-page 2 --output-dir output --log-level INFO
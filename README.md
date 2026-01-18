# Job Application Assistant

A Python-based tool for scraping and automating job application data. Built with **Poetry**, **Playwright**, and **BeautifulSoup**, this project collects job postings from Dice and exports them into structured formats for easy processing, analysis, or further automation.

## Features

- Scrapes job listings from Dice.
- Outputs job data in formats like JSONL and CSV.
- Supports scalable scraping with pagination control.
- Built-in testing, code formatting, and linting with **pytest**, **Black**, and **Ruff**.
- CI-ready with **GitHub Actions**.

## Installation

### Prerequisites
Make sure you have **Python 3.12** installed.

### Install Poetry
Poetry is used to manage dependencies and virtual environments. Install it globally with:

```bash
pip install poetry
poetry --version

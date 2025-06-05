# General Web Scraper for Data Collection

## Overview

This Python script (`general_scraper.py`) is a tool designed to search the web using DuckDuckGo and scrape content from the resulting pages. It includes functionality for basic keyword spotting to identify pages potentially relevant to user-defined topics. The primary goal of this version is to collect publicly available information for research and informational purposes.

## Features

*   **Web Search:** Uses DuckDuckGo to perform web searches based on a user query.
*   **Page Scraping:** Navigates to search result links and extracts textual content from web pages.
*   **Keyword Spotting:** Identifies a predefined list of keywords within the scraped text.
*   **Configurable Headless Mode:** Can run with a visible browser window (for observation) or headlessly (for automated runs).
*   **Rate Limiting:** Includes delays between requests to be respectful to web servers.
*   **Basic Ethical Safeguards:** Includes disclaimers, console warnings, and placeholders for `robots.txt` compliance and advanced content filtering.

## How it Works

1.  **Driver Initialization (`init_driver`):** Sets up an undetected_chromedriver instance. It can be run in headless or non-headless mode.
2.  **Web Search (`search_web`):**
    *   Takes a search query.
    *   Navigates to DuckDuckGo and performs the search.
    *   Parses the search results page to extract links.
3.  **Page Scraping (`scrape_page`):**
    *   For each link obtained from the search:
        *   (Placeholder) Checks `robots.txt` (currently prints a reminder).
        *   Navigates to the page URL.
        *   Extracts textual content from common HTML tags (`<article>`, `<main>`, `<p>`, etc.).
        *   Performs keyword spotting on the extracted text using a predefined list (`DEMO_KEYWORDS`).
        *   Returns a dictionary containing the URL, HTML/text snippets, found keywords, and a flag indicating if relevant content was found.
4.  **Visual Feedback:** When not in headless mode, the browser window shows the navigation. Extensive print statements log the script's actions to the console.

## Ethical Use and Disclaimer

This script is intended for collecting publicly available information for research and informational purposes, particularly for understanding online content trends.

**Users MUST ensure their use of this tool complies with all applicable laws, regulations, and website terms of service. Misuse of this tool for promoting hate speech, illegal activities, or any form of harassment is strictly prohibited.**

The keywords used (`DEMO_KEYWORDS` in the script) are for demonstration and initial filtering. They are not exhaustive and may require significant refinement for specific research goals. The interpretation of scraped data requires careful human oversight and contextual understanding.

**BE RESPONSIBLE AND ETHICAL IN YOUR USE OF THIS TOOL.**

## Future Improvements (Suggestions)

*   Full `robots.txt` parsing and compliance.
*   Dynamic scrolling logic (scroll until no new content loads).
*   More sophisticated text extraction (e.g., using libraries like `articlextractor` or `trafilatura`).
*   Advanced NLP for contextual analysis rather than simple keyword spotting.
*   GUI for easier use.
*   Database integration for storing results.

# --- ETHICAL USE AND DISCLAIMER ---
# This script is intended for collecting publicly available information for research and informational purposes
# related to understanding extremist activities and propaganda.
#
# Users MUST ensure their use of this tool complies with all applicable laws, regulations,
# and website terms of service. Misuse of this tool for promoting hate speech, illegal activities,
# or any form of harassment is strictly prohibited.
#
# The keywords used are for demonstration and initial filtering. They are not exhaustive
# and may require significant refinement. The interpretation of scraped data requires
# careful human oversight and contextual understanding.
#
# BE RESPONSIBLE AND ETHICAL IN YOUR USE OF THIS TOOL.
# --- END DISCLAIMER ---

import time
import undetected_chromedriver as uc
import json
import os
import random
import re # For regex-based selectors and link finding
from bs4 import BeautifulSoup
import datetime # For main test block example
from urllib.parse import urlencode, urlparse, parse_qs

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
]

# Initial list of keywords for demonstration.
# WARNING: This list is for initial technical demonstration only and is not exhaustive, definitive,
# or representative of a complete or nuanced understanding of extremist content.
# It requires careful review and expansion by subject matter experts.
DEMO_KEYWORDS = ['violence', 'hate speech', 'propaganda', 'extremism', 'radicalization']


def init_driver(headless=True, user_agent_arg=None, proxy_server=None, browser_version=None):
    options = uc.ChromeOptions()
    selected_user_agent = user_agent_arg or random.choice(USER_AGENTS)
    options.add_argument(f'--user-agent={selected_user_agent}')
    # print(f"WebDriver User-Agent selected: {selected_user_agent}") # Reduced noise for this test
    if headless:
        options.add_argument('--headless=new'); options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080'); options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage'); options.add_argument("--disable-blink-features=AutomationControlled")
    if proxy_server: options.add_argument(f'--proxy-server={proxy_server}')
    driver = None
    try:
        print(f"Attempting to initialize driver for Chrome version: {browser_version if browser_version else 'auto-detected'}")
        driver = uc.Chrome(options=options, version_main=browser_version if browser_version else None)
        if driver: driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception as e:
        print(f"Error initializing undetected_chromedriver: {e}")
        if driver: driver.quit()
        return None
    return driver

def check_robots_txt(url_to_check):
    """
    Placeholder function for checking robots.txt.
    In a real deployment, this would fetch and parse robots.txt.
    """
    # TODO: Implement actual robots.txt fetching and parsing.
    # For now, this is a placeholder demonstrating where the check would go.
    # Note: Proper robots.txt handling requires parsing the file from the site's root
    # (e.g., http://example.com/robots.txt) and respecting its directives.
    try:
        parsed_url = urlparse(url_to_check)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        print(f"[INFO] Placeholder: In a real deployment, check robots.txt for {base_url} before scraping {url_to_check}.")
    except Exception as e:
        print(f"[WARN] Could not parse URL for robots.txt check: {url_to_check} - {e}")

def scrape_page(driver, page_url):
    """
    Scrapes a generic web page for content.
    Note: Selectors will need to be generalized or made configurable.
    """
    check_robots_txt(page_url) # Call robots.txt check before accessing the page.

    # Consider more formal logging here
    print(f"\n[INFO] Attempting to scrape page: {page_url}")
    raw_html_snippet = ""
    extracted_text = ""
    found_keywords_on_page = []
    has_relevant_content = False

    try:
        driver.get(page_url)
        # Ethical consideration: Add a delay to avoid overwhelming servers.
        print(f"[INFO] Waiting after page load for {page_url}...")
        time.sleep(random.uniform(2, 5)) # Rate limiting

        print(f"Navigated to {page_url}. Waiting for initial page load...")
        # Initial sleep, can be replaced by explicit waits later
        # This sleep was already here, the one above is the new rate limit for after GET.
        time.sleep(random.uniform(3, 5))

        # TODO: Implement dynamic scrolling until no new significant content loads or timeout.
        scroll_attempts = 5
        # print(f"[DEBUG] Scrolling {scroll_attempts} time(s) to load content...") # Less verbose for now
        for i in range(scroll_attempts):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1.0, 1.5))

        # print("[DEBUG] Finished scrolling. Retrieving page source...") # Less verbose for now
        page_source = driver.page_source
        raw_html_snippet = page_source[:500] + "..."
        soup = BeautifulSoup(page_source, "html.parser")

        # Text extraction strategy
        # Consider more formal logging for verbosity of strategy if needed
        texts = []
        main_content_tags = ['article', 'main'] # Prioritize these
        for tag_name in main_content_tags:
            elements = soup.find_all(tag_name)
            for el in elements:
                texts.append(el.get_text(separator='\n', strip=True))

        if not texts or len(" ".join(texts)) < 500:
            # print("[DEBUG] Primary content tags (article, main) yielded little text, trying p, h1-h3, common divs.")
            secondary_tags = ['p', 'h1', 'h2', 'h3', 'div']
            for tag_name in secondary_tags:
                elements = soup.find_all(tag_name)
                for el in elements:
                    # Basic filter for divs: avoid divs with too many sub-divs or script/style tags
                    if tag_name == 'div':
                        if el.find_all(['script', 'style', 'form', 'nav']): # Skip if it seems like a structural/nav div
                            continue
                        if len(el.find_all('div')) > 5 : # Heuristic: skip divs that are mostly containers for other divs
                            continue
                    texts.append(el.get_text(separator='\n', strip=True))

        if not texts or len(" ".join(texts)) < 200:
            # print("[DEBUG] Still not much text, falling back to body text.")
            body_element = soup.find('body')
            if body_element:
                texts.append(body_element.get_text(separator='\n', strip=True))

        extracted_text = "\n".join(texts)
        # print(f"[DEBUG] Total extracted text length: {len(extracted_text)}") # Optional: for debugging text length
        extracted_text_lower = extracted_text.lower()

        # Keyword Spotting
        # TODO: Implement advanced content filtering here to avoid processing/storing highly offensive material beyond simple keyword presence.
        for keyword in DEMO_KEYWORDS:
            if keyword.lower() in extracted_text_lower:
                found_keywords_on_page.append(keyword)

        if found_keywords_on_page:
            has_relevant_content = True
            # Consider more formal logging here
            print(f"[INFO] Keywords found on {page_url}: {found_keywords_on_page}")
            print(f"[INFO] Snippet of text with keywords (first 200 chars of extracted text): {extracted_text[:200]}...")
        # else:
            # print(f"[INFO] No keywords found on {page_url}") # Can be verbose

    except Exception as e:
        # Consider more formal logging here
        print(f"[ERROR] Error during scraping page {page_url}: {type(e).__name__} - {e}")
        # Return partial data if an error occurs mid-process
        return {
            "url": page_url,
            "raw_html_snippet": raw_html_snippet,
            "extracted_text_snippet": extracted_text[:500] + "..." if extracted_text else "",
            "found_keywords": found_keywords_on_page,
            "has_relevant_content": has_relevant_content,
            "error": str(e)
        }

    return {
        "url": page_url,
        "raw_html_snippet": raw_html_snippet,
        "extracted_text_snippet": extracted_text[:500] + "..." if extracted_text else "",
        "found_keywords": found_keywords_on_page,
        "has_relevant_content": has_relevant_content
    }

def search_web(driver, query, search_engine_url="https://duckduckgo.com/"):
    """
    Performs a web search using the specified search engine and query.
    Extracts links from the first page of results.
    Default is DuckDuckGo.
    """
    # For DuckDuckGo, the main query parameter is 'q'.
    # The URL structure is typically https://duckduckgo.com/?q=your+query
    search_query_encoded = urlencode({'q': query})
    if "duckduckgo.com" in search_engine_url: # Ensure correct construction for DDG
        full_search_url = f"{search_engine_url}?{search_query_encoded}"
    else: # Keep flexibility for other engines if specified
        full_search_url = f"{search_engine_url}?{search_query_encoded}"
        # Note: this might need adjustment if other engines use different param names than 'q'

    # Consider more formal logging here for production use
    print(f"[INFO] Performing search for query: '{query}' on {search_engine_url}")
    print(f"[INFO] Navigating to search URL: {full_search_url}")

    extracted_links = []
    try:
        driver.get(full_search_url)
        # Ethical consideration: Add a delay to avoid overwhelming servers.
        print(f"[INFO] Waiting after search page load for {full_search_url}...")
        time.sleep(random.uniform(2, 5)) # Rate limiting

        # TODO: Replace with explicit wait for better reliability
        # time.sleep(random.uniform(2, 4)) # This was the original DDG wait, now covered by rate limit above.

        page_source = driver.page_source
        print(f"Page source snippet (first 500 chars):\n{page_source[:500]}") # DEBUGGING: Print page source

        soup = BeautifulSoup(page_source, "html.parser")

        # DuckDuckGo specific selectors
        # Results are often in articles with class "nrn-react-div" or divs with "result" in class name
        # Links are often <a> tags with class like "result__a" or within an <h2> with class "result__title"

        # Primary strategy: Find result containers and then the main link within them.
        # Selectors based on observed DDG structures (mid-2024 and before). May need frequent updates.

        # Try modern article-based selectors first
        result_containers = soup.find_all('article', class_=re.compile(r'(react-results--mainline-article|wLL07_0Xnd1QZpzpfR4W)'))

        if not result_containers: # Fallback to older div-based structure
            results_wrapper = soup.find('div', id=re.compile(r'links|results'))
            if results_wrapper:
                result_containers = results_wrapper.find_all('div', class_=re.compile(r'\bresult\b|\bweb-result\b', re.IGNORECASE))
            else: # If no main wrapper, search globally for result divs (less precise)
                result_containers = soup.find_all('div', class_=re.compile(r'\bresult\b|\bweb-result\b', re.IGNORECASE))

        if not result_containers: # Even broader, look for any article tag if specific ones failed
             result_containers = soup.find_all('article')

        # Consider more formal logging here
        print(f"[INFO] Found {len(result_containers)} potential result containers on page.")

        for article_or_div in result_containers:
            # Inside each container, find the main link.
            # Common patterns:
            # 1. <a> tag with data-testid="result-title-a"
            # 2. <a> tag child of <h2> with class containing "result__title"
            # 3. <a> tag with class containing "result__a"

            link_tag = article_or_div.find('a', attrs={"data-testid": "result-title-a"}, href=True)

            if not link_tag:
                title_h2 = article_or_div.find('h2', class_=re.compile(r'result__title', re.IGNORECASE))
                if title_h2:
                    link_tag = title_h2.find('a', href=True)

            if not link_tag: # Broader fallback for a link within the article/div that might be a result
                 link_tag = article_or_div.find('a', class_=re.compile(r'result__a',re.IGNORECASE), href=True)

            if link_tag:
                href = link_tag.get('href')
                if href:
                    # Filter out known non-result patterns for DDG
                    # DDG links are generally direct, but some internal / redirectors might exist.
                    # For example, links starting with "/l/" are DDG redirects.
                    if href.startswith("/l/"): # Handle DDG redirects
                        parsed_url = urlparse(href) # Ensure urllib.parse.urlparse is used
                        params = parse_qs(parsed_url.query) # Ensure urllib.parse.parse_qs is used
                        if 'uddg' in params and params['uddg'][0].startswith('http'):
                            extracted_links.append(params['uddg'][0])
                        # else: print(f"Found DDG redirect but no 'uddg' param: {href}")
                    elif href.startswith("http"): # Direct external links
                        if not "duckduckgo.com/y.js" in href: # Filter out tracking scripts
                            extracted_links.append(href)
                            # Consider more formal logging here
                            # print(f"[DEBUG] Extracted link: {href}")
                    # Other relative links are ignored for now unless a clear pattern for results is found.

            if len(extracted_links) >= 20: # Limit results
                # print("[INFO] Reached link extraction limit (20).") # Optional: log limit reached
                break

        # Deduplicate links while preserving order
        seen = set()
        extracted_links = [x for x in extracted_links if not (x in seen or seen.add(x))]

        # Consider more formal logging here
        if extracted_links:
            print(f"[INFO] Extracted {len(extracted_links)} unique links for query '{query}'. First 5:")
            for i, link in enumerate(extracted_links[:5]):
                print(f"  {i+1}. {link}")
            if len(extracted_links) > 5:
                print(f"  ... and {len(extracted_links) - 5} more.")
        elif not result_containers:
            print(f"[INFO] No potential result containers found for query '{query}'.")
        else: # Containers found, but no links extracted
            print(f"[INFO] No links extracted from {len(result_containers)} potential containers for query '{query}'.")
            if result_containers: # If result_containers is not empty and no links extracted
                 print("[DEBUG] Printing first few container snippets if no links were extracted:")
                 for i, r_container in enumerate(result_containers[:2]):
                     print(f"  Debug DDG Container {i}:\n{str(r_container)[:200]}...")


    except Exception as e:
        # Consider more formal logging here
        print(f"[ERROR] Error during web search for '{query}': {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()

    # print(f"Extracted {len(extracted_links)} links for query '{query}'.") # Replaced by more detailed print above
    return extracted_links

# Removed placeholder functions: scrape_profile, scrape_group, scrape_search

if __name__ == '__main__':
    print("--- General Scraper Test Block ---")

    print("""
    --- ETHICAL USE REMINDER ---
    This script is for research and informational purposes.
    Users MUST comply with laws, regulations, and website terms of service.
    Misuse for promoting hate speech, illegal activities, or harassment is prohibited.
    BE RESPONSIBLE AND ETHICAL.
    ---
    """)

    # Test search_web
    print("\n--- Testing search_web & scrape_page ---")
    # Try to force Chrome version 136 for the test.
    driver = init_driver(headless=False, browser_version=136)
    if driver:
        try:
            search_query = "news analysis of online propaganda" # Updated query
            results_to_scrape = 5 # Updated number of results to scrape

            print(f"Performing search for: \"{search_query}\" using default DuckDuckGo")

            search_results_links = search_web(driver, search_query)

            if search_results_links:
                print(f"\nFound {len(search_results_links)} links from search. Scraping first {results_to_scrape}...")
                for i, link_url in enumerate(search_results_links[:results_to_scrape]): # Scrape specified number of links
                    print(f"\n--- Scraping link {i+1}: {link_url} ---")
                    scraped_data = scrape_page(driver, link_url)
                    print("Scraped Data:")
                    for key, value in scraped_data.items():
                        if isinstance(value, str) and len(value) > 100: # Print snippets for long strings
                             print(f"  {key}: {value[:100]}...")
                        else:
                             print(f"  {key}: {value}")
                    print("--- Finished scraping link ---")
            else:
                print("No links found from search to scrape.")

        except Exception as e:
            print(f"An error occurred during the main test block: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("\nPausing for a few seconds before closing browser...")
            time.sleep(5)
            driver.quit()
            print("Driver quit.")
    else:
        print("Failed to initialize driver for the test block.")

    print("\n--- General Scraper Test Block Finished ---")

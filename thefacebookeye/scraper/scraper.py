import time
import undetected_chromedriver as uc
import json
import os
import random
import re # For regex-based selectors and link finding
from bs4 import BeautifulSoup
import datetime # For main test block example

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0",
]

def init_driver(headless=True, user_agent_arg=None, proxy_server=None):
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
        driver = uc.Chrome(options=options)
        if driver: driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception as e:
        print(f"Error initializing undetected_chromedriver: {e}")
        if driver: driver.quit()
        return None
    return driver

def load_cookies(driver, cookies_file="cookies.json"):
    if not os.path.exists(cookies_file): print(f"Cookie file '{cookies_file}' not found."); return
    current_url = "";
    try: current_url = driver.current_url
    except Exception: current_url = "about:blank"
    if not ("facebook.com" in current_url):
        try: driver.get("https://www.facebook.com"); time.sleep(random.uniform(1.5,2.5)) # Adjusted sleep
        except Exception as e: print(f"Error navigating to Facebook for cookies: {e}"); return
    try:
        with open(cookies_file, 'r') as f: cookies = json.load(f)
    except Exception as e: print(f"Error loading/parsing cookies from '{cookies_file}': {e}"); return
    for cookie in cookies:
        if not all(field in cookie for field in ['name', 'value']): continue
        if 'expires' in cookie and isinstance(cookie['expires'], (int, float)):
            cookie['expiry'] = int(cookie['expires']); del cookie['expires']
        if 'domain' in cookie and cookie['domain'] == 'facebook.com': cookie['domain'] = '.facebook.com'
        try: driver.add_cookie(cookie)
        except Exception as e: print(f"Warning: Could not add cookie {cookie.get('name')}: {e}")
    # print(f"Attempted to load cookies from '{cookies_file}'.") # Reduce noise

def scrape_page(driver, page_url):
    """
    Scrapes a Facebook page for posts, including link extraction from post text.
    Note: Selectors are illustrative and will need ongoing refinement for live Facebook.
    """
    print(f"Attempting to scrape live page for posts and links: {page_url}")
    extracted_posts = []
    try:
        driver.get(page_url)
        print(f"Navigated to {page_url}. Waiting for initial page load...")
        time.sleep(random.uniform(3, 5)) # Reduced sleep
        scroll_attempts = 1 # Further reduced for this specific test with invalid URL
        print(f"Scrolling {scroll_attempts} time(s) to load posts...")
        for i in range(scroll_attempts):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            scroll_wait = random.uniform(1, 2) # Reduced sleep
            # print(f"  Scroll {i+1}/{scroll_attempts}, waiting {scroll_wait:.2f}s...")
            time.sleep(scroll_wait)
        print("Finished scrolling. Retrieving page source...")
        page_source = driver.page_source
    except Exception as e:
        print(f"Error during navigation or scrolling for {page_url}: {type(e).__name__} - {e}")
        if "example.invalid" in page_url or "ERR_NAME_NOT_RESOLVED" in str(e):
             print("This error is expected for the dummy/invalid URL used in testing.")
        return []

    soup = BeautifulSoup(page_source, "html.parser")
    # print("Analyzing page source for posts and links...") # Reduce noise

    potential_post_elements = soup.find_all(attrs={'role': 'article'})
    # print(f"Found {len(potential_post_elements)} potential post elements (role=article).")

    for i, el in enumerate(potential_post_elements):
        post_data = {
            "post_id": None, "permalink": None, "text": None, "timestamp_str": None,
            "author_name": None, "author_url": None, "source_page_url": page_url,
            "extracted_links": [],
            "raw_html_snippet": str(el)[:100] + "..."
        }

        author_link_el = el.find('a', href=re.compile(r"/(?:[^/]+/)?(?:profile\.php\?id=\d+|[^/]+(?:/(?!(posts|videos|photos)/))?$|pg/[^/]+/)"))
        if author_link_el and not any(kw in author_link_el.get('href','') for kw in ['sharer.php', 'permalink.php', '/posts/', '/videos/', '/photos/']):
            post_data["author_name"] = author_link_el.get_text(strip=True) or "Unknown"
            href = author_link_el['href']; post_data["author_url"] = f"https://www.facebook.com{href}" if href.startswith('/') else href

        post_content_area = el.find('div', attrs={'data-ad-preview': 'message'}) or el.find('div', dir='auto')
        if post_content_area:
            post_data["text"] = post_content_area.get_text(separator='\n', strip=True)
            links_in_post = set()
            # Extract from <a> tags within the post content
            for link_tag in post_content_area.find_all('a', href=True):
                href = link_tag['href']
                # Basic filter: ensure it's an absolute link and not to facebook.com itself from within post text
                if href.startswith('http') and 'facebook.com' not in href:
                    links_in_post.add(href)

            # Extract from plain text using regex (more prone to false positives if not careful)
            # This regex is a common one, but might need refinement.
            plaintext_url_pattern = r'(?:(?:https?|ftp)://|www\.)(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?(?:/?|[/?]\S+)'
            if post_data["text"]: # Ensure text is not None
                found_in_text = re.findall(plaintext_url_pattern, post_data["text"], re.IGNORECASE)
                for url in found_in_text:
                    # Ensure it's a full URL for consistency, and filter out facebook.com links
                    if not url.startswith(('http', 'ftp')): url = 'http://' + url
                    if 'facebook.com' not in url:
                        links_in_post.add(url)
            post_data["extracted_links"] = list(links_in_post)

        permalink_tag_el = el.find('a', href=re.compile(r"(/posts/|/videos/\d+|/permalink\.php|story_fbid=|photo\.php\?fbid=)"), title=True)                         or el.find('a', href=re.compile(r"(/posts/|/videos/\d+|/permalink\.php|story_fbid=|photo\.php\?fbid=)"))
        if permalink_tag_el:
            href = permalink_tag_el['href']
            post_data["permalink"] = f"https://www.facebook.com{href}" if href.startswith('/') else href
            post_data["timestamp_str"] = permalink_tag_el.get('title', permalink_tag_el.get_text(strip=True))
            match = re.search(r"(?:posts/|videos/|story_fbid=|fbid=|php\?story_fbid=)(\d+)", href)
            if match: post_data["post_id"] = match.group(1)

        if post_data["text"] or post_data["permalink"] or post_data["author_name"]:
            # print(f"  Post {i+1}: Author '{post_data['author_name']}', Links: {len(post_data['extracted_links'])}, Text: '{str(post_data['text'])[:20]}...'")
            extracted_posts.append(post_data)

    # print(f"Finished live scraping for {page_url}. Extracted {len(extracted_posts)} posts.")
    return extracted_posts

def scrape_profile(driver, profile_url): print(f"Placeholder: Scraping profile {profile_url}"); return []
def scrape_group(driver, group_url): print(f"Placeholder: Scraping group {group_url}"); return []
def scrape_search(driver, query, location=None): print(f"Placeholder: Scraping search for '{query}'"); return []

if __name__ == '__main__':
    print("--- Scraper Main Test Block ---")
    print("\n--- Testing WebDriver Initialization ---")
    init_success_count = 0
    test_driver_init = init_driver(headless=True)
    if test_driver_init:
        init_success_count += 1
        try:
            ua = test_driver_init.execute_script("return navigator.userAgent;")
            wb_flag = test_driver_init.execute_script("return navigator.webdriver;")
            print(f"  Init Test UA: {ua[:40]}..., WebDriver Flag: {wb_flag}")
        except Exception as e: print(f"  Error with test driver init: {e}")
        finally: test_driver_init.quit()
    else: print("  Failed to init test driver for UA test.")
    print(f"Init test: {init_success_count} successful initializations.")

    print("\n--- Testing scrape_page (live logic with dummy URL, expecting 0 posts) ---")
    main_driver = init_driver(headless=True)
    if main_driver:
        test_url_live_logic = "https://example.invalid/dummy_fb_page_for_links"
        print(f"Calling scrape_page with dummy URL: {test_url_live_logic}")
        scraped_data = scrape_page(main_driver, test_url_live_logic)
        print(f"scrape_page with dummy URL returned {len(scraped_data)} posts.")
        if scraped_data:
             print(f"  Content of first item (if any): Links found: {len(scraped_data[0].get('extracted_links',[]))}")

        main_driver.quit()
        print("Main driver quit after live logic test.")
    else:
        print("Failed to initialize main driver for scrape_page live logic test.")
    print("\n--- Scraper Main Test Block Finished ---")

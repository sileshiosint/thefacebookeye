import time
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import os

def init_driver(headless=True, user_agent=None):
    """Initializes and returns an undetected ChromeDriver instance."""
    options = Options()
    if headless:
        options.add_argument('--headless')
        options.add_argument('--disable-gpu') # Often recommended with headless
        options.add_argument('--window-size=1920,1080') # Standardize window size
    if user_agent:
        options.add_argument(f'user-agent={user_agent}')

    # options.add_argument('--no-sandbox') # Use if issues occur in certain environments
    # options.add_argument('--disable-dev-shm-usage') # Use if issues occur in certain environments
    driver = uc.Chrome(options=options)
    print("WebDriver initialized.")
    return driver

def load_cookies(driver, cookies_file="cookies.json"):
    """Loads cookies from a JSON file into the WebDriver session."""
    if not os.path.exists(cookies_file):
        print(f"Cookie file '{cookies_file}' not found. Proceeding without loading cookies.")
        return

    # Navigate to a base Facebook domain before adding cookies
    # This is often required by WebDriver for cookies to be set correctly.
    current_url = driver.current_url
    if not (current_url.startswith("https://www.facebook.com") or \
            current_url.startswith("https://facebook.com") or \
            current_url == "data:,"): # Check for initial blank page
        print(f"Navigating to facebook.com to set cookies. Current URL: {current_url}")
        driver.get("https://www.facebook.com")
        time.sleep(2) # Allow page to load
    elif current_url == "data:,": # Specifically handle if current url is blank
        print(f"Current URL is blank ('data:,'). Navigating to facebook.com to set cookies.")
        driver.get("https://www.facebook.com")
        time.sleep(2)


    try:
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{cookies_file}'. Ensure it's valid JSON.")
        return
    except Exception as e:
        print(f"Error loading cookies from '{cookies_file}': {e}")
        return

    for cookie in cookies:
        required_fields = ['name', 'value']
        if not all(field in cookie for field in required_fields):
            print(f"Skipping cookie due to missing fields: {cookie.get('name', 'Unnamed cookie')}")
            continue

        if 'expires' in cookie and isinstance(cookie['expires'], (int, float)):
            cookie['expiry'] = int(cookie['expires'])
            del cookie['expires']

        # Ensure domain has a leading dot if it's for the base domain, e.g., ".facebook.com"
        if 'domain' in cookie and cookie['domain'] == 'facebook.com':
            cookie['domain'] = '.facebook.com'
        elif 'domain' in cookie and not cookie['domain'].startswith('.'):
             # Be cautious about modifying domains too much, but a common case is ensuring leading dot for subdomains too
             pass


        try:
            driver.add_cookie(cookie)
        except Exception as e:
            problematic_cookie_info = {k: cookie.get(k) for k in ['name', 'domain', 'path']}
            print(f"Warning: Could not add cookie {problematic_cookie_info}: {e}")

    print(f"Successfully attempted to load cookies from '{cookies_file}'.")

# Dummy HTML for development - this is crucial as we can't make live calls
dummy_post_html_for_testing = '''
<article aria-label="Post">
  <div>
    <header> <!-- Added header for author -->
      <a href="/someuserprofile?id=123" aria-label="Author Name">Author Name</a>
    </header>
    <div>
      <div dir="auto" style="text-align: start;">This is the post text. #hashtag1 Visit example.com.</div>
    </div>
    <footer> <!-- Added footer for permalink -->
      <a href="/permalink/1234567890/">
        <abbr title="January 1, 2023 at 10:00 AM">10h</abbr>
      </a>
    </footer>
  </div>
</article>
<article aria-label="Story"> <!-- Test with "Story" as well -->
  <div>
    <header>
      <a href="/anotherpage?id=456" aria-label="Page Name">Page Name</a>
    </header>
    <div>
      <div dir="auto" style="text-align: start;">Another post, with more content. #example #testing. Check out another-example.com.</div>
    </div>
    <footer>
      <a href="/posts/0987654321/">
        <abbr title="January 2, 2023 at 12:00 PM">1d</abbr>
      </a>
    </footer>
  </div>
</article>
'''

def scrape_page(driver, page_url):
    """Scrapes a Facebook page for posts. (Basic Implementation using BeautifulSoup)"""
    print(f"Attempting to scrape page: {page_url}")
    # In a real scenario, you would uncomment the following lines:
    # driver.get(page_url)
    # print(f"Navigated to {page_url}. Waiting for page to load and scroll...")
    # time.sleep(5) # Initial load
    # Perform scrolling here to load more posts
    # for _ in range(3): # Example: scroll 3 times
    #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #     time.sleep(3)
    # page_source = driver.page_source

    print("INFO: Using DUMMY HTML for scrape_page development. Selectors WILL need live testing and refinement.")
    page_source = f'''
    <html><head><title>Dummy Page</title></head><body>
        <div id="feed_container">
            {dummy_post_html_for_testing}
        </div>
    </body></html>
    '''

    soup = BeautifulSoup(page_source, "html.parser")
    extracted_posts = []

    potential_posts = soup.find_all('article', attrs={'aria-label': lambda x: x and x.lower() in ['post', 'story', 'update']})
    if not potential_posts: # Fallback selector
        potential_posts = soup.find_all('div', attrs={'role': 'article'})


    print(f"Found {len(potential_posts)} potential post elements using current selectors.")

    for i, post_element in enumerate(potential_posts):
        post_data = {
            "post_id": None, "permalink": None, "text": None,
            "timestamp_str": None, "author_name": None, "author_url": None,
            "source_page_url": page_url,
            "raw_html_snippet": str(post_element)[:250] + "..."
        }

        author_container = post_element.find('header')
        if author_container:
            author_link = author_container.find('a', attrs={'aria-label': True, 'href': True})
            if author_link:
                 post_data["author_name"] = author_link.get_text(strip=True) or author_link.get('aria-label')
                 href = author_link['href']
                 post_data["author_url"] = f"https://www.facebook.com{href}" if href.startswith('/') else href

        text_container = post_element.find('div', attrs={'dir': 'auto'})
        if text_container:
            text_parts = []
            for elem in text_container.descendants:
                if isinstance(elem, str):
                    text_parts.append(elem.strip())
                elif elem.name == 'br':
                    text_parts.append('\\n') # Correctly escape newline for string
            post_data["text"] = " ".join(filter(None, text_parts)).strip()
            post_data["extracted_urls_from_text"] = [word for word in post_data["text"].split() if "http" in word or ".com" in word]

        permalink_container = post_element.find('footer')
        if permalink_container:
            permalink_tag = permalink_container.find('a', href=lambda x: x and any(kw in x for kw in ['/posts/', '/permalink/', 'story_fbid=', 'photo.php?fbid=', '/videos/']))
            if permalink_tag:
                href = permalink_tag['href']
                post_data["permalink"] = f"https://www.facebook.com{href}" if href.startswith('/') else href

                try:
                    if '/posts/' in href: post_data["post_id"] = href.split('/posts/')[1].split('/')[0].split('?')[0]
                    elif '/permalink/' in href: post_data["post_id"] = href.split('/permalink/')[1].split('/')[0].split('?')[0]
                    elif 'story_fbid=' in href: post_data["post_id"] = href.split('story_fbid=')[1].split('&')[0]
                    elif 'photo.php?fbid=' in href: post_data["post_id"] = href.split('fbid=')[1].split('&')[0]
                    elif '/videos/' in href: post_data["post_id"] = href.split('/videos/')[1].split('/')[0].split('?')[0]
                except IndexError:
                    print(f"Warning: Could not parse post_id from permalink: {href}")

                timestamp_abbr = permalink_tag.find('abbr')
                if timestamp_abbr and timestamp_abbr.get('title'):
                    post_data["timestamp_str"] = timestamp_abbr['title']
                else: # Fallback if abbr or title not found
                    post_data["timestamp_str"] = permalink_tag.get_text(strip=True)

        if post_data["text"] or post_data["permalink"]:
            print(f"  Successfully extracted data for potential post #{i+1}")
            extracted_posts.append(post_data)
        else:
            print(f"  Skipping potential post #{i+1} as no key data (text/permalink) was extracted. HTML: {str(post_element)[:100]}...")

    if not extracted_posts:
        print("No posts extracted. Check selectors or HTML structure if this was a live page.")

    print(f"Finished scraping {page_url}. Extracted {len(extracted_posts)} posts.")
    return extracted_posts

def scrape_profile(driver, profile_url):
    """Placeholder for scraping a public Facebook profile. Will use similar logic to scrape_page based on observed HTML structure."""
    print(f"Placeholder: Scraping profile {profile_url} - will use logic similar to scrape_page.")
    return {"url": profile_url, "data": "dummy profile data from placeholder"}

def scrape_group(driver, group_url):
    """Placeholder for scraping a public Facebook group. Will use similar logic to scrape_page, focusing on group feed structure."""
    print(f"Placeholder: Scraping group {group_url} - will use logic similar to scrape_page.")
    return {"url": group_url, "data": "dummy group data from placeholder"}

def scrape_search(driver, query, location=None):
    """Placeholder for scraping Facebook search results. Structure is different and will require specific selectors and logic."""
    search_url = f"https://www.facebook.com/search/posts/?q={query}"
    print(f"Placeholder: Scraping search for '{query}' at '{search_url}'")
    return {"query": query, "data": "dummy search results from placeholder"}

if __name__ == '__main__':
    print("Starting basic scraper test...")
    driver = None
    try:
        driver = init_driver(headless=True)

        if driver:
            print("Driver initialized successfully.")

            print("Attempting to load default cookies.json...")
            load_cookies(driver)
            print("Attempting to load non_existent_cookies.json...")
            load_cookies(driver, cookies_file="non_existent_cookies.json")

            print("\n--- Testing scrape_page (with dummy HTML) ---")
            scraped_page_data = scrape_page(driver, "https://www.facebook.com/examplepage.dummy")
            if scraped_page_data:
                print(f"scrape_page returned {len(scraped_page_data)} items.")
                for idx, p_data in enumerate(scraped_page_data):
                    print(f"  Post {idx+1} Author: {p_data.get('author_name')}, ID: {p_data.get('post_id')}, Text snippet: {p_data.get('text', '')[:50]}...")
            else:
                print("scrape_page returned no data from dummy HTML.")

            print("\n--- Calling other placeholder scrape functions ---")
            scrape_profile(driver, "https://www.facebook.com/exampleprofile.dummy")
            scrape_group(driver, "https://www.facebook.com/groups/examplegroup.dummy")
            scrape_search(driver, "example keyword dummy")

            print("\nPlaceholder functions (excluding scrape_page actual test) called.")

        else:
            print("Driver initialization failed.")

    except Exception as e:
        print(f"An error occurred in main: {e}")
        # Detailed error for debugging:
        import traceback
        print(traceback.format_exc())

    finally:
        if driver:
            driver.quit()
            print("WebDriver closed.")
    print("\nBasic scraper test finished.")

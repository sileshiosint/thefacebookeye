import time
import datetime
import os # Added for sys.path manipulation
import sys # Added for sys.path manipulation

# Conditional import for celery_app for direct script execution vs. Celery worker
if __name__ == '__main__' and __package__ is None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from scheduler.celery_app import celery_app
else:
    from .celery_app import celery_app

from config_loader import load_config, DEFAULT_CONFIG_PATH, EXAMPLE_CONFIG_PATH
from scraper.scraper import init_driver, scrape_page, scrape_group, scrape_search, load_cookies
from database.mongo_handler import connect_db, insert_many_posts

@celery_app.task(name="scheduler.tasks.collect_data_task", bind=True) # Added bind=True
def collect_data_task(self): # Added self for bind=True
    """
    Celery task to collect data from configured Facebook targets.
    """
    task_start_time = datetime.datetime.utcnow()
    # Access task ID via self.request.id when bind=True
    task_id = self.request.id if self.request.id else "N/A_direct_run"

    print(f"[{task_start_time.isoformat()}] Starting data collection task (ID: {task_id})...")

    config = load_config()
    if not config:
        message = "Failed to load configuration. Aborting task."
        print(message)
        return {"status": "error", "message": message, "start_time": task_start_time.isoformat(), "end_time": datetime.datetime.utcnow().isoformat()}

    target_pages = config.get('target_pages', [])
    target_groups = config.get('target_groups', [])
    target_keywords = config.get('target_keywords', [])

    driver = None
    db_conn = None
    all_inserted_ids = []
    errors = []
    processed_targets = 0

    try:
        print("Initializing WebDriver...")
        driver = init_driver(headless=True)
        if not driver:
            raise Exception("Failed to initialize WebDriver (driver is None).")

        print("Attempting to load cookies...")
        load_cookies(driver)

        print("Connecting to MongoDB...")
        db_conn = connect_db()
        if not db_conn:
            print("Warning: Failed to connect to MongoDB. Scraped data will not be saved.")

        if target_pages:
            print(f"Processing {len(target_pages)} target pages...")
            for page_url in target_pages:
                processed_targets +=1
                print(f"Scraping page: {page_url}")
                try:
                    scraped_data_list = scrape_page(driver, page_url)

                    if scraped_data_list:
                        posts_to_insert = []
                        for idx, item in enumerate(scraped_data_list):
                            transformed_post = {
                                "platform": "Facebook", "type": "page_post_scheduled",
                                "source_url_scraped": page_url,
                                "page_metadata": {"name": item.get("author_name", page_url.split('/')[-1]), "url": page_url},
                                "author": {"name": item.get("author_name"), "profile_url": item.get("author_url")},
                                "post": {
                                    "id": item.get("post_id", f"scraped_{page_url.split('/')[-1]}_{idx}_{int(time.time())}"),
                                    "text": item.get("text"),
                                    "timestamp_str": item.get("timestamp_str"),
                                    "permalink": item.get("permalink"),
                                    "extracted_links": item.get("extracted_links", []),
                                    # Link extraction field will be added here by the modifier script later
                                },
                                "scraped_at_utc": datetime.datetime.utcnow().isoformat(),
                                "celery_task_id": task_id
                            }
                            posts_to_insert.append(transformed_post)

                        if posts_to_insert:
                            if db_conn:
                                print(f"Attempting to insert {len(posts_to_insert)} posts from {page_url} into MongoDB...")
                                inserted_ids = insert_many_posts(db_conn, posts_to_insert)
                                if inserted_ids:
                                    all_inserted_ids.extend(inserted_ids)
                                    print(f"Successfully processed insert_many_posts for {page_url}, {len(inserted_ids)} ID(s) returned by function.")
                            else:
                                print(f"Data ready for DB: {len(posts_to_insert)} posts from {page_url}, but DB connection is unavailable.")
                        else:
                            print(f"No data extracted or transformed for {page_url}.")
                    elif db_conn is None and scraped_data_list: # This condition might be redundant due to earlier check
                         print(f"Scraped {len(scraped_data_list)} items from {page_url}, but DB connection is unavailable.")
                    else:
                        print(f"No data returned from scrape_page for {page_url}.")
                except Exception as e:
                    err_msg = f"Error scraping page {page_url}: {type(e).__name__} - {e}"
                    print(err_msg)
                    errors.append(err_msg)
                print(f"Short delay after scraping {page_url}...")
                time.sleep(2)
        else:
            print("No target pages configured.")

        if target_groups:
            print(f"Processing {len(target_groups)} target groups (placeholder)...")
        if target_keywords:
            print(f"Processing {len(target_keywords)} target keywords (placeholder)...")
        print("Data collection attempt finished.")
    except Exception as e:
        err_msg = f"A critical error occurred in collect_data_task: {type(e).__name__} - {e}"
        print(err_msg)
        errors.append(err_msg)
    finally:
        if driver:
            print("Closing WebDriver...")
            driver.quit()

    task_end_time = datetime.datetime.utcnow()
    summary = {
        "status": "completed_with_errors" if errors else "completed_successfully",
        "targets_processed_attempt": processed_targets,
        "total_inserted_posts": len(all_inserted_ids),
        "errors": errors,
        "start_time_utc": task_start_time.isoformat(),
        "end_time_utc": task_end_time.isoformat(),
        "duration_seconds": (task_end_time - task_start_time).total_seconds()
    }
    print(f"Task Summary: {summary}")
    return summary

if __name__ == '__main__':
    print("--- Running collect_data_task directly for testing ---")
    print("NOTE: This test requires config.json, and potentially MongoDB and network access for WebDriver.")

    if not os.path.exists(DEFAULT_CONFIG_PATH) and os.path.exists(EXAMPLE_CONFIG_PATH):
        print(f"Copying '{EXAMPLE_CONFIG_PATH}' to '{DEFAULT_CONFIG_PATH}' for test run...")
        import shutil
        shutil.copy(EXAMPLE_CONFIG_PATH, DEFAULT_CONFIG_PATH)
    elif not os.path.exists(DEFAULT_CONFIG_PATH) and not os.path.exists(EXAMPLE_CONFIG_PATH):
        print(f"Error: Neither '{DEFAULT_CONFIG_PATH}' nor '{EXAMPLE_CONFIG_PATH}' found. Task cannot run.")
        sys.exit(1) # Okay to exit in __main__ for direct script run

    # To simulate a Celery task context for `self.request.id`
    class MockCeleryTask:
        def __init__(self):
            self.request = MockRequest()

    class MockRequest:
        def __init__(self, id=None):
            self.id = id or "direct_test_run_" + str(int(time.time()))

    # Instantiate the mock task and call the method bound to it
    # mock_task_instance = MockCeleryTask() # Old approach
    # final_result = collect_data_task(mock_task_instance) # Old approach, caused TypeError

    # Corrected approach using apply() for tasks with bind=True
    # The 'request' object will be automatically available as self.request
    mock_req_obj = MockRequest()
    result = collect_data_task.apply(request=mock_req_obj)
    # .get() will raise an exception if the task itself raised one.
    # Otherwise, it returns the task's return value.
    try:
        final_result = result.get()
    except Exception as e:
        print(f"Task execution failed with an exception: {e}")
        import traceback
        print(traceback.format_exc())
        final_result = {"status": "error_in_test_harness", "message": str(e)}


    print(f"\nTest run result: {final_result}")
    print("--- Direct test finished ---")

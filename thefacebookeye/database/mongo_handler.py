import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure
import datetime

DEFAULT_CONNECTION_STRING = "mongodb://localhost:27017/"
DEFAULT_DB_NAME = "thefacebookeye"
DEFAULT_COLLECTION_NAME = "posts"

def connect_db(connection_string=DEFAULT_CONNECTION_STRING, db_name=DEFAULT_DB_NAME):
    """
    Establishes a connection to MongoDB and returns the database object.
    Returns None if connection fails.
    """
    try:
        client = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        print(f"Successfully connected to MongoDB: {client.server_info().get('version', 'unknown version')} at {connection_string.split('@')[-1] if '@' in connection_string else connection_string}.")
        db = client[db_name]
        return db
    except ConnectionFailure:
        print(f"Error: Failed to connect to MongoDB at {connection_string}.")
        print("Please ensure MongoDB is running and accessible.")
        return None
    except Exception as e: # Catch other potential errors like auth issues if connection_string has user/pass
        print(f"An unexpected error occurred during MongoDB connection: {e}")
        return None

def insert_post(db, post_data, collection_name=DEFAULT_COLLECTION_NAME):
    """
    Inserts a single post document into the specified collection.
    Adds an 'inserted_at_db' timestamp to the document.
    Returns the inserted_id if successful, None otherwise.
    """
    if not db:
        print("Error: No database connection provided to insert_post.")
        return None

    collection = db[collection_name]
    post_data_to_insert = post_data.copy()
    post_data_to_insert['inserted_at_db'] = datetime.datetime.utcnow()

    try:
        result = collection.insert_one(post_data_to_insert)
        print(f"Successfully inserted post with id {result.inserted_id} into '{collection_name}'.")
        return result.inserted_id
    except OperationFailure as e:
        print(f"Error: MongoDB operation failed during insert_post: {e.details if hasattr(e, 'details') else e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during insert_post: {e}")
        return None

def insert_many_posts(db, posts_list, collection_name=DEFAULT_COLLECTION_NAME):
    """
    Inserts a list of post documents into the specified collection.
    Adds an 'inserted_at_db' timestamp to each document.
    Returns a list of inserted_ids of successfully inserted documents.
    Returns empty list if input is empty or db connection fails or BulkWriteError occurs.
    Returns None if a major unexpected exception occurs.
    """
    if not db:
        print("Error: No database connection provided to insert_many_posts.")
        return [] # Return empty list for consistency on "no successful inserts"
    if not posts_list:
        print("Info: No posts provided to insert_many_posts.")
        return []

    collection = db[collection_name]
    processed_posts_list = []
    for post_data in posts_list:
        post_copy = post_data.copy()
        post_copy['inserted_at_db'] = datetime.datetime.utcnow()
        processed_posts_list.append(post_copy)

    try:
        result = collection.insert_many(processed_posts_list, ordered=False)
        print(f"Successfully inserted {len(result.inserted_ids)} posts into '{collection_name}'.")
        return result.inserted_ids
    except pymongo.errors.BulkWriteError as bwe:
        print(f"Warning: MongoDB bulk write error during insert_many_posts.")
        # For ordered=False, result.inserted_ids on the BulkWriteError object itself is not standard.
        # The original result object before exception might have it, but it's not accessible here.
        # bwe.details['nInserted'] gives the count of successfully inserted documents.
        print(f"  Successfully inserted {bwe.details.get('nInserted', 0)} out of {len(posts_list)} attempted posts.")
        print(f"  Error details: {bwe.details}")
        # It's complex to get the IDs of successfully inserted items from bwe.details without more parsing.
        # Returning an empty list to signify that not all (or maybe none) were inserted as requested.
        return []
    except OperationFailure as e:
        print(f"Error: MongoDB operation failed during insert_many_posts: {e.details if hasattr(e, 'details') else e}")
        return None # Major operation failure
    except Exception as e:
        print(f"An unexpected error occurred during insert_many_posts: {e}")
        return None # Other major unexpected error

if __name__ == '__main__':
    print("--- Testing MongoDB Handler ---")
    # Attempt to connect to MongoDB.
    db_connection = connect_db()

    if db_connection:
        print(f"Connected to database: {db_connection.name}")
        test_collection_name = "test_posts_collection"
        print(f"Using test collection: {test_collection_name}")
        test_collection = db_connection[test_collection_name]

        # Cleanup: Ensure test collection is empty before tests
        print(f"Cleaning up '{test_collection_name}' before tests...")
        test_collection.delete_many({})


        # 1. Test insert_post
        print("\n--- Test 1: Inserting a single dummy post ---")
        dummy_post_data = {
            "platform": "Facebook", "type": "page_post_test",
            "source": {"name": "Test Page", "url": "http://example.com/page", "verified": False},
            "author": {"name": "Test Author", "profile_url": "http://example.com/author", "is_page": False},
            "post": {
                "id": "test_post_001", "text": "Hello MongoDB from mongo_handler.py!",
                "timestamp_str": str(datetime.datetime.utcnow()), "permalink": "http://example.com/post/001",
            },
            "scraped_at": datetime.datetime.utcnow()
        }

        inserted_id = insert_post(db_connection, dummy_post_data, collection_name=test_collection_name)
        if inserted_id:
            print(f"Single post inserted with ID: {inserted_id}")
            found_post = test_collection.find_one({"_id": inserted_id})
            if found_post and found_post["post"]["id"] == "test_post_001":
                print(f"Successfully retrieved inserted post: ID {found_post['post']['id']}")
            else:
                print(f"Error: Could not retrieve or verify the inserted post with ID {inserted_id}.")
        else:
            print("Failed to insert single dummy post. Check MongoDB connection and logs.")

        # 2. Test insert_many_posts
        print("\n--- Test 2: Inserting multiple dummy posts ---")
        dummy_posts_list = [
            {**dummy_post_data, "post": {**dummy_post_data["post"], "id": "test_multi_002", "text": "Multi-post 1"}},
            {**dummy_post_data, "post": {**dummy_post_data["post"], "id": "test_multi_003", "text": "Multi-post 2"}},
            # Add a deliberately malformed post to test BulkWriteError (e.g. duplicate _id if we were setting it)
            # For now, let's assume valid posts for simplicity of checking counts
        ]

        inserted_ids_list = insert_many_posts(db_connection, dummy_posts_list, collection_name=test_collection_name)

        # inserted_ids_list could be None (major error), empty (BulkWriteError or no posts), or list of IDs.
        if inserted_ids_list is not None:
            print(f"insert_many_posts operation finished. {len(inserted_ids_list)} ID(s) returned by function.")
            if inserted_ids_list: # If function returned any IDs
                 print(f"  IDs: {inserted_ids_list}")

            # Verify count in DB
            count_after_insert = test_collection.count_documents({"post.id": {"$in": ["test_multi_002", "test_multi_003"]}})
            print(f"Found {count_after_insert} posts in DB matching test criteria for multi-insert.")

            if len(inserted_ids_list) == len(dummy_posts_list) and count_after_insert == len(dummy_posts_list):
                print(f"Successfully inserted and verified all {count_after_insert} posts.")
            elif inserted_ids_list: # Some were inserted according to function return
                 print(f"Multi-insert seems partially successful or verification mismatch. Function returned {len(inserted_ids_list)} IDs, DB has {count_after_insert} matching posts.")
            else: # inserted_ids_list was empty, but not None
                print("No posts confirmed inserted by insert_many_posts (empty ID list returned), or a BulkWriteError occurred where no IDs were successfully returned by the function.")
        else: # insert_many_posts returned None (major error)
            print("Failed to insert multiple dummy posts due to a major error. Check MongoDB connection and logs.")

        # Final cleanup of test collection content
        print(f"Cleaning up '{test_collection_name}' after tests...")
        test_collection.delete_many({})
        if test_collection.count_documents({}) == 0:
            print(f"Test collection '{test_collection_name}' is now empty.")
            # Optionally drop the collection if it's truly temporary and should not persist
            # db_connection.drop_collection(test_collection_name)
            # print(f"Dropped empty test collection: {test_collection_name}")
        else:
            print(f"Warning: Test collection '{test_collection_name}' not empty after cleanup.")

    else:
        print("MongoDB connection not established. Skipping actual database interaction tests.")
        print("The mongo_handler.py script is syntactically valid but could not connect to a DB.")

    print("\n--- MongoDB Handler Test Finished ---")

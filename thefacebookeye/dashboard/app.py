from flask import Flask, render_template, request
import sys
import os
from bson.objectid import ObjectId # For querying by _id if needed

# Adjust path to import from parent directory modules
try:
    from database.mongo_handler import connect_db, DEFAULT_DB_NAME, DEFAULT_COLLECTION_NAME
except ImportError:
    print("Attempting to add project root to sys.path for module resolution in app.py...")
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_script_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Added {project_root} to sys.path")
    from database.mongo_handler import connect_db, DEFAULT_DB_NAME, DEFAULT_COLLECTION_NAME

app = Flask(__name__)

def format_post(post):
    if post.get('_id') and isinstance(post['_id'], ObjectId):
        post['_id_str'] = str(post['_id'])
    post['source'] = post.get('source', {})
    post['author'] = post.get('author', {})
    post['post_data'] = post.get('post', {})
    post['language_analysis'] = post.get('language_analysis', {})
    post['nlp_features'] = post.get('nlp_features', {})
    post['post_data']['text'] = post['post_data'].get('text', 'N/A')
    post['author']['name'] = post['author'].get('name', 'Unknown Author')
    post['post_data']['timestamp_str'] = post['post_data'].get('timestamp_str', 'N/A')
    post['risk_score'] = post.get('risk_score', 0.0)
    post['post_data']['id'] = post['post_data'].get('id', 'N/A')
    post['post_data']['permalink'] = post['post_data'].get('permalink')
    return post

@app.route('/', methods=['GET'])
def dashboard():
    db = connect_db()
    posts_list = []
    error_message = None
    search_keyword = request.args.get('keyword', default='').strip()
    min_risk_score_str = request.args.get('min_risk_score', default='').strip()
    query = {}
    if search_keyword:
        query["$or"] = [
            {"post.text": {"$regex": search_keyword, "$options": "i"}},
            {"author.name": {"$regex": search_keyword, "$options": "i"}},
            {"page_metadata.name": {"$regex": search_keyword, "$options": "i"}},
        ]
    min_risk_score_val = None
    if min_risk_score_str:
        try:
            min_risk_score_val = float(min_risk_score_str)
            query["risk_score"] = {"$gte": min_risk_score_val}
        except ValueError:
            error_message = "Invalid minimum risk score. Please enter a number."
            return render_template('dashboard.html', posts=[], error_message=error_message,
                                   search_keyword=search_keyword, min_risk_score=min_risk_score_str)
    if db:
        try:
            posts_cursor = db[DEFAULT_COLLECTION_NAME].find(query).sort("inserted_at_db", -1).limit(100)
            processed_posts_list = [format_post(post) for post in posts_cursor]
        except Exception as e:
            error_message = f"Error fetching posts from MongoDB: {e}"
            processed_posts_list = []
    else:
        error_message = "Failed to connect to MongoDB. Please ensure it's running and accessible."
        processed_posts_list = []
    return render_template('dashboard.html',
                           posts=processed_posts_list,
                           error_message=error_message,
                           search_keyword=search_keyword,
                           min_risk_score=min_risk_score_str)

if __name__ == '__main__':
    print("Starting Flask development server...")
    print("Dashboard will be available at http://127.0.0.1:5005/")
    print("Ensure MongoDB is running and potentially populated with data for full functionality.")
    app.run(debug=True, port=5005, host='0.0.0.0')

import os
import json
import webbrowser
from flask import Flask, render_template_string, request, jsonify
from dotenv import load_dotenv
import boto3
from botocore.config import Config

load_dotenv()

app = Flask(__name__, static_url_path='', static_folder='.')

B2_ACCESS_KEY = os.getenv("B2_ACCESS_KEY")
B2_SECRET_KEY = os.getenv("B2_SECRET_KEY")
B2_ENDPOINT_URL = os.getenv("B2_ENDPOINT_URL")
BUCKET_NAME = os.getenv("BUCKET_NAME")
OBJECT_NAME = os.getenv("OBJECT_NAME")

s3_client = boto3.client(
    service_name="s3",
    endpoint_url=B2_ENDPOINT_URL,
    aws_access_key_id=B2_ACCESS_KEY,
    aws_secret_access_key=B2_SECRET_KEY,
    config=Config(signature_version="s3v4")
)

def get_data_from_cloud():
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=OBJECT_NAME)
        file_content = response['Body'].read().decode('utf-8')
        return json.loads(file_content)
    except Exception:
        return {}

@app.route('/')
def index():
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return render_template_string(html_content)

@app.route('/api/status')
def status():
    data = get_data_from_cloud()
    return jsonify({"total_crawled": len(data)})

@app.route('/api/search')
def search():
    query = request.args.get('q', '').strip().lower()
    if not query:
        return jsonify({"results": [], "total_crawled": 0})
        
    query_words = [word for word in query.split() if word]
    data = get_data_from_cloud()
    search_results = []
    
    for url, site_info in data.items():
        # חזרה למבנה המקורי: תומך בטקסט פשוט או מחלץ את שדה התוכן אם מדובר במילון
        if isinstance(site_info, dict):
            content = site_info.get("content", "")
        else:
            content = str(site_info)
            
        content_lower = content.lower()
        
        if all(word in content_lower for word in query_words):
            total_matches = sum(content_lower.count(word) for word in query_words)
            
            # יצירת סניפט קצר ובטוח ללא קריסות שרת
            snippet = content[:200] + "..."
            if query_words:
                first_word = query_words[0]
                start_idx = content_lower.find(first_word)
                if start_idx != -1:
                    start = max(0, start_idx - 40)
                    end = min(len(content), start_idx + 160)
                    snippet = content[start:end] + "..."
                    
            search_results.append({
                "url": url,
                "content": content, # מעבירים את כל התוכן ל-HTML שהג'אווהסקריפט יחלץ כותרת
                "score": total_matches,
                "snippet": snippet
            })
            
    search_results.sort(key=lambda x: x["score"], reverse=True)
    return jsonify({"results": search_results, "total_crawled": len(data)})

if __name__ == '__main__':
    webbrowser.open("http://127.0.0.1:5000")
    app.run(port=5000, debug=False)

import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import boto3
from botocore.config import Config

s3_client = boto3.client(
    service_name="s3",
    endpoint_url=os.environ.get("B2_ENDPOINT_URL"),
    aws_access_key_id=os.environ.get("B2_ACCESS_KEY"),
    aws_secret_access_key=os.environ.get("B2_SECRET_KEY"),
    config=Config(signature_version="s3v4")
)

def get_data_from_cloud():
    try:
        response = s3_client.get_object(
            Bucket=os.environ.get("BUCKET_NAME"), 
            Key=os.environ.get("OBJECT_NAME")
        )
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception:
        return {}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        if parsed_url.path == '/api/status':
            data = get_data_from_cloud()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.end_headers()
            self.wfile.write(json.dumps({"total_crawled": len(data)}).encode())
            return
            
        elif parsed_url.path == '/api/search':
            # שליפת מילת החיפוש מהפרמטר q
            query_list = query_params.get('q', [''])
            query = query_list[0].strip().lower() if query_list else ''
            
            if not query:
                response_data = {"results": [], "total_crawled": 0}
            else:
                query_words = [word for word in query.split() if word]
                data = get_data_from_cloud()
                search_results = []
                
                for url, site_info in data.items():
                    # בדיקה יציבה: תמיכה בפורמט הישן (מחרוזת) ובפורמט החדש (מילון)
                    if isinstance(site_info, str):
                        title = url
                        content = site_info
                    elif isinstance(site_info, dict):
                        title = site_info.get("title", url)
                        content = site_info.get("content", "")
                    else:
                        continue
                        
                    content_lower = content.lower()
                    if all(word in content_lower for word in query_words):
                        total_matches = sum(content_lower.count(word) for word in query_words)
                        
                        # הפקת תקציר טקסט בטוחה ללא קריסות
                        first_word = query_words[0] if query_words else ""
                        start_idx = content_lower.find(first_word)
                        
                        if start_idx != -1:
                            start = max(0, start_idx - 40)
                            end = min(len(content), start_idx + 150)
                            snippet = content[start:end]
                        else:
                            snippet = content[:150]
                            
                        search_results.append({
                            "url": url,
                            "title": title,
                            "score": total_matches,
                            "snippet": snippet
                        })
                        
                search_results.sort(key=lambda x: x["score"], reverse=True)
                response_data = {"results": search_results, "total_crawled": len(data)}

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:;")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            return

        self.send_response(404)
        self.end_headers()

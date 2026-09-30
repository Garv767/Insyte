from http.server import BaseHTTPRequestHandler
import urllib.parse
from ._db import get_connection, execute_query, send_json_response

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path.rstrip("/")
        params = dict(urllib.parse.parse_qsl(parsed_path.query))

        try:
            if path.endswith("/semantic"):
                query = params.get("q", "")
                data = self._semantic_search_mock(query)
                send_json_response(self, 200, data)
            else:
                send_json_response(self, 404, {"error": f"Unknown path: {path}"})
        except Exception as e:
            send_json_response(self, 500, {"error": str(e)})

    def _semantic_search_mock(self, query: str) -> list:
        # Mock response for UI functionality
        return [
            {
                "stock_code": "B089234X",
                "description": f"AI Match for: {query}",
                "unit_price": 45.99,
                "revenue": 12500,
                "avg_rating": 4.5,
                "review_count": 320,
                "similarity_score": 0.94,
                "cosine_distance": 0.06
            },
            {
                "stock_code": "B079124Y",
                "description": "Similar Semantic Item",
                "unit_price": 29.99,
                "revenue": 8400,
                "avg_rating": 4.2,
                "review_count": 150,
                "similarity_score": 0.88,
                "cosine_distance": 0.12
            }
        ]

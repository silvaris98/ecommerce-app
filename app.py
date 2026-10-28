from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import json

EXTERNAL_API = "https://dummyjson.com/products?limit=10"


class EcommerceHandler(BaseHTTPRequestHandler):

    def send_json(self, status, body):
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"status": "healthy"})
            return

        if self.path == "/api/products":
            try:
                with urlopen(EXTERNAL_API, timeout=5) as response:
                    data = json.loads(
                        response.read().decode("utf-8")
                    )

                products = [
                    {
                        "id": item["id"],
                        "name": item["title"],
                        "price": item["price"],
                        "image": item["thumbnail"]
                    }
                    for item in data.get("products", [])
                ]

                self.send_json(200, {
                    "source": "DummyJSON",
                    "products": products
                })

            except (URLError, HTTPError, TimeoutError,
                    ValueError, KeyError) as error:
                self.send_json(502, {
                    "error": "External products API unavailable",
                    "detail": str(error)
                })
            return

        self.send_json(200, {
            "app": "Sample E-commerce Store",
            "message": "Welcome to our online store!",
            "endpoints": ["/health", "/api/products"]
        })


HTTPServer(("0.0.0.0", 8000), EcommerceHandler).serve_forever()

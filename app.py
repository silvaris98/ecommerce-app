
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import json

EXTERNAL_API = "https://dummyjson.com/products?limit=10"


class EcommerceHandler(BaseHTTPRequestHandler):

    def send_json(self, status, body):
        data = json.dumps(body).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()

        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"status": "healthy"})
            return

        if self.path == "/api/products":
            try:
                request = Request(
                    EXTERNAL_API,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "application/json"
                    }
                )

                with urlopen(request, timeout=10) as response:
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
                    "total": len(products),
                    "products": products
                })

            except (HTTPError, URLError, TimeoutError,
                    ValueError, KeyError) as error:
                self.send_json(502, {
                    "error": "External products API unavailable",
                    "detail": str(error)
                })

            return

        if self.path == "/":
            self.send_json(200, {
                "app": "Sample E-commerce Store",
                "message": "Welcome to our online store!",
                "endpoints": [
                    "/",
                    "/health",
                    "/api/products"
                ]
            })
            return

        self.send_json(404, {
            "error": "Not found",
            "path": self.path
        })

    def log_message(self, format, *args):
        print(
            "%s - - [%s] %s"
            % (
                self.address_string(),
                self.log_date_time_string(),
                format % args
            ),
            flush=True
        )


if __name__ == "__main__":
    server = HTTPServer(
        ("0.0.0.0", 8000),
        EcommerceHandler
    )

    print("E-commerce server running on port 8000", flush=True)
    server.serve_forever()

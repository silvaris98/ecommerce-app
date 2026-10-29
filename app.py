from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
import json
import os
import sqlite3

EXTERNAL_API = "https://dummyjson.com/products?limit=10"
DB_PATH = os.environ.get("DB_PATH", "/data/ecommerce.db")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


class EcommerceHandler(BaseHTTPRequestHandler):

    def send_json(self, status, body):
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            try:
                with sqlite3.connect(DB_PATH, timeout=3) as conn:
                    conn.execute("SELECT 1")
                self.send_json(200, {
                    "status": "healthy",
                    "database": "connected"
                })
            except sqlite3.Error:
                self.send_json(503, {
                    "status": "unhealthy",
                    "database": "unavailable"
                })
            return

        if path == "/api/orders":
            try:
                with sqlite3.connect(DB_PATH, timeout=3) as conn:
                    conn.row_factory = sqlite3.Row
                    rows = conn.execute(
                        "SELECT id, customer_name, product_name, "
                        "quantity, created_at FROM orders ORDER BY id DESC"
                    ).fetchall()

                self.send_json(200, {
                    "total": len(rows),
                    "orders": [dict(row) for row in rows]
                })
            except sqlite3.Error:
                self.send_json(500, {"error": "Could not read orders"})
            return

        if path == "/api/products":
            try:
                request = Request(
                    EXTERNAL_API,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "application/json"
                    }
                )

                with urlopen(request, timeout=10) as response:
                    data = json.loads(response.read().decode("utf-8"))

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

            except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as error:
                self.send_json(502, {
                    "error": "External products API unavailable",
                    "detail": str(error)
                })
            return

        if path == "/":
            self.send_json(200, {
                "app": "Sample E-commerce Store",
                "message": "Welcome to our online store!",
                "endpoints": [
                    "/", "/health", "/api/products", "/api/orders"
                ]
            })
            return

        self.send_json(404, {"error": "Not found", "path": path})

    def do_POST(self):
        path = urlparse(self.path).path

        if path != "/api/orders":
            self.send_json(404, {"error": "Not found", "path": path})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 10000:
                self.send_json(400, {"error": "Invalid request body size"})
                return

            payload = json.loads(self.rfile.read(length).decode("utf-8"))

            customer = payload.get("customer_name")
            product = payload.get("product_name")
            quantity = payload.get("quantity")

            if (
                not isinstance(customer, str) or not customer.strip()
                or len(customer) > 100
                or not isinstance(product, str) or not product.strip()
                or len(product) > 200
                or type(quantity) is not int or not 1 <= quantity <= 1000
            ):
                self.send_json(400, {
                    "error": "Provide customer_name, product_name and quantity (1-1000)"
                })
                return

            with sqlite3.connect(DB_PATH, timeout=3) as conn:
                cursor = conn.execute(
                    "INSERT INTO orders (customer_name, product_name, quantity) "
                    "VALUES (?, ?, ?)",
                    (customer.strip(), product.strip(), quantity)
                )
                order_id = cursor.lastrowid

            self.send_json(201, {
                "message": "Order saved",
                "order_id": order_id
            })

        except (ValueError, UnicodeDecodeError):
            self.send_json(400, {"error": "Invalid JSON"})
        except sqlite3.Error:
            self.send_json(500, {"error": "Could not save order"})

    def log_message(self, format, *args):
        print(
            "%s - - [%s] %s" % (
                self.address_string(),
                self.log_date_time_string(),
                format % args
            ),
            flush=True
        )


if __name__ == "__main__":
    init_db()
    server = HTTPServer(("0.0.0.0", 8000), EcommerceHandler)
    print("E-commerce server running on port 8000", flush=True)
    server.serve_forever()

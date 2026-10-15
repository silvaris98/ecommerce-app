from http.server import BaseHTTPRequestHandler, HTTPServer
import json

PRODUCTS = [
    {"id": 1, "name": "Laptop", "price": 150000},
    {"id": 2, "name": "Headphones", "price": 8500},
    {"id": 3, "name": "Keyboard", "price": 4500}
]

class EcommerceHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = {"status": "healthy"}
            self.send_response(200)
        elif self.path == "/api/products":
            body = {"products": PRODUCTS}
            self.send_response(200)
        else:
            body = {
                "app": "Sample E-commerce Store",
                "message": "Welcome to our online store!",
                "endpoints": ["/health", "/api/products"]
            }
            self.send_response(200)

        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

HTTPServer(("0.0.0.0", 8000), EcommerceHandler).serve_forever()

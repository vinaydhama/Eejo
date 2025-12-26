
# WebServerLib.py
import http.server
import socketserver
import os
from pathlib import Path
from typing import Optional





class WebServer:
    PORT = 8002
    HTTPIP= "0.0.0.0"
    httpd=""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000, relative_webroot: Optional[str] = None) -> None:
        self.host = host
        self.port = port
        self.httpd = None

        # Default webroot path
        if relative_webroot is None:
            relative_webroot = os.path.join("templates", "Eejo_SwimManagerWeb")

        base_dir = Path(__file__).resolve().parent
        self.webroot = (base_dir / relative_webroot).resolve()

        if not self.webroot.exists():
            raise FileNotFoundError(f"Web root not found: {self.webroot}")

    def start(self) -> None:
        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True

        handler = http.server.SimpleHTTPRequestHandler
        kwargs = {"directory": str(self.webroot)}

        self.httpd = ReusableTCPServer((self.host, self.port), lambda *a, **k: handler(*a, **kwargs))
        print(f"Serving {self.webroot} at http://{self.host}:{self.port}")
        try:
            self.httpd.serve_forever()
        finally:
            self.stop()

    def stop(self) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None

#!/usr/bin/env python3
import json, ssl, time, os, hmac, hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

SECRETS_FILE = "/var/doppler/secrets.json"
HMAC_SECRET = os.getenv("DOPPLER_HMAC_SECRET", "default_secret")

class DopplerHandler(BaseHTTPRequestHandler):
    def _verify_hmac(self, body, hmac_header, timestamp_str):
        try:
            timestamp = int(timestamp_str)
            if abs(time.time() - timestamp) > 300: return False
            payload = f"{timestamp}:{body.decode()}".encode()
            expected = hmac.new(HMAC_SECRET.encode(), payload, hashlib.sha256).hexdigest()
            return hmac.compare_digest(hmac_header, expected)
        except: return False
    
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        elif self.path == "/secrets":
            try:
                with open(SECRETS_FILE) as f:
                    secrets = json.load(f)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(secrets).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_POST(self):
        if self.path == "/secrets/update":
            hmac_header = self.headers.get("X-HMAC", "")
            timestamp_str = self.headers.get("X-Timestamp", "")
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len)
            if not self._verify_hmac(body, hmac_header, timestamp_str):
                self.send_response(401)
                self.end_headers()
                return
            try:
                new_secrets = json.loads(body)
                if os.path.exists(SECRETS_FILE):
                    os.system(f"cp {SECRETS_FILE} {SECRETS_FILE}.backup")
                with open(SECRETS_FILE, "w") as f:
                    json.dump(new_secrets, f, indent=2)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"updated": datetime.now().isoformat()}).encode())
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

if __name__ == "__main__":
    os.makedirs("/var/doppler", exist_ok=True)
    if not os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, "w") as f:
            json.dump({"artusi_habibot": {}, "polytubot": {}, "casa": {}}, f, indent=2)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain("/etc/doppler/pki/server.crt", "/etc/doppler/pki/server.key")
    context.load_verify_locations("/etc/doppler/pki/ca.crt")
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False
    server = HTTPServer(("0.0.0.0", 8443), DopplerHandler)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    print("[Doppler] mTLS server running on https://0.0.0.0:8443")
    server.serve_forever()

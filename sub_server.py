#!/usr/bin/env python3
import argparse
import base64
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote

def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "y", "on")

def getenv(name: str, default: str = "") -> str:
    return os.getenv(name, default)

def identity():
    return {
        "uuid": getenv("UUID"),
        "reality_public_key": getenv("REALITY_PUBLIC_KEY"),
        "short_id": getenv("SHORT_ID"),
        "anytls_password": getenv("ANYTLS_PASSWORD"),
        "sni": getenv("SNI", "adm.com"),
        "node_name": getenv("NODE_NAME", "private-node"),
        "public_host": getenv("PUBLIC_HOST", ""),
        "vless_tcp_port": int(getenv("EXTERNAL_VLESS_TCP_PORT", getenv("VLESS_TCP_PORT", "443"))),
        "vless_hu_port": int(getenv("EXTERNAL_VLESS_HU_PORT", getenv("VLESS_HU_PORT", "8443"))),
        "anytls_port": int(getenv("EXTERNAL_ANYTLS_PORT", getenv("ANYTLS_PORT", "9443"))),
        "vless_hu_path": getenv("VLESS_HU_PATH", "/up"),
    }

def build_config():
    sni = getenv("SNI", "adm.com")
    block_private = env_bool("BLOCK_PRIVATE", True)
    block_bt = env_bool("BLOCK_BITTORRENT", True)

    rules = []
    if block_private:
        rules.append({"ip_is_private": True, "action": "reject"})
    if block_bt:
        rules.append({"protocol": "bittorrent", "action": "reject"})

    common_reality = {
        "enabled": True,
        "handshake": {"server": sni, "server_port": 443},
        "private_key": getenv("REALITY_PRIVATE_KEY"),
        "short_id": [getenv("SHORT_ID")],
    }

    return {
        "log": {"level": getenv("LOG_LEVEL", "warn"), "timestamp": True},
        "inbounds": [
            {
                "type": "vless",
                "tag": "vless-tcp-reality",
                "listen": "::",
                "listen_port": int(getenv("VLESS_TCP_PORT", "443")),
                "users": [{"name": "user", "uuid": getenv("UUID"), "flow": ""}],
                "tls": {
                    "enabled": True,
                    "server_name": sni,
                    "reality": common_reality,
                },
            },
            {
                "type": "vless",
                "tag": "vless-httpupgrade-reality",
                "listen": "::",
                "listen_port": int(getenv("VLESS_HU_PORT", "8443")),
                "users": [{"name": "user", "uuid": getenv("UUID"), "flow": ""}],
                "tls": {
                    "enabled": True,
                    "server_name": sni,
                    "reality": common_reality,
                },
                "transport": {
                    "type": "httpupgrade",
                    "host": sni,
                    "path": getenv("VLESS_HU_PATH", "/up"),
                },
            },
            {
                "type": "anytls",
                "tag": "anytls-reality",
                "listen": "::",
                "listen_port": int(getenv("ANYTLS_PORT", "9443")),
                "users": [{"name": "user", "password": getenv("ANYTLS_PASSWORD")}],
                "tls": {
                    "enabled": True,
                    "server_name": sni,
                    "reality": common_reality,
                },
            },
        ],
        "outbounds": [{"type": "direct", "tag": "direct"}],
        "route": {"rules": rules, "final": "direct"},
    }

def vless_uri_tcp(i):
    host = i["public_host"] or "YOUR_PUBLIC_HOST"
    name = quote(f'{i["node_name"]}-vless-tcp')
    return (
        f'vless://{i["uuid"]}@{host}:{i["vless_tcp_port"]}'
        f'?encryption=none&security=reality&sni={i["sni"]}'
        f'&fp=chrome&pbk={i["reality_public_key"]}&sid={i["short_id"]}'
        f'&type=tcp#{name}'
    )

def vless_uri_hu(i):
    host = i["public_host"] or "YOUR_PUBLIC_HOST"
    name = quote(f'{i["node_name"]}-vless-httpupgrade')
    return (
        f'vless://{i["uuid"]}@{host}:{i["vless_hu_port"]}'
        f'?encryption=none&security=reality&sni={i["sni"]}'
        f'&fp=chrome&pbk={i["reality_public_key"]}&sid={i["short_id"]}'
        f'&type=httpupgrade&host={i["sni"]}&path={quote(i["vless_hu_path"], safe="")}'
        f'#{name}'
    )

def anytls_uri(i):
    # URI support differs by client. /client.json is the more reliable import format.
    host = i["public_host"] or "YOUR_PUBLIC_HOST"
    name = quote(f'{i["node_name"]}-anytls-reality')
    return (
        f'anytls://{quote(i["anytls_password"], safe="")}@{host}:{i["anytls_port"]}'
        f'?security=reality&sni={i["sni"]}&pbk={i["reality_public_key"]}&sid={i["short_id"]}'
        f'#{name}'
    )

def client_json(i):
    host = i["public_host"] or "YOUR_PUBLIC_HOST"
    return {
        "log": {"level": "warn", "timestamp": True},
        "outbounds": [
            {
                "type": "vless",
                "tag": "vless-tcp-reality",
                "server": host,
                "server_port": i["vless_tcp_port"],
                "uuid": i["uuid"],
                "tls": {
                    "enabled": True,
                    "server_name": i["sni"],
                    "utls": {"enabled": True, "fingerprint": "chrome"},
                    "reality": {"enabled": True, "public_key": i["reality_public_key"], "short_id": i["short_id"]},
                },
            },
            {
                "type": "vless",
                "tag": "vless-httpupgrade-reality",
                "server": host,
                "server_port": i["vless_hu_port"],
                "uuid": i["uuid"],
                "tls": {
                    "enabled": True,
                    "server_name": i["sni"],
                    "utls": {"enabled": True, "fingerprint": "chrome"},
                    "reality": {"enabled": True, "public_key": i["reality_public_key"], "short_id": i["short_id"]},
                },
                "transport": {"type": "httpupgrade", "host": i["sni"], "path": i["vless_hu_path"]},
            },
            {
                "type": "anytls",
                "tag": "anytls-reality",
                "server": host,
                "server_port": i["anytls_port"],
                "password": i["anytls_password"],
                "tls": {
                    "enabled": True,
                    "server_name": i["sni"],
                    "utls": {"enabled": True, "fingerprint": "chrome"},
                    "reality": {"enabled": True, "public_key": i["reality_public_key"], "short_id": i["short_id"]},
                },
            },
        ],
    }

def sub_plain():
    i = identity()
    return "\n".join([vless_uri_tcp(i), vless_uri_hu(i), anytls_uri(i)]) + "\n"

def sub_base64():
    return base64.urlsafe_b64encode(sub_plain().encode()).decode()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/health"):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok\n")
            return
        if self.path.startswith("/client.json"):
            body = json.dumps(client_json(identity()), indent=2, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.startswith("/sub.b64"):
            body = (sub_base64() + "\n").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.startswith("/") or self.path.startswith("/sub"):
            body = sub_plain().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-config")
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()

    if args.write_config:
        cfg = build_config()
        with open(args.write_config, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return

    if args.serve:
        port = int(getenv("SUB_PORT", "8080"))
        server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
        print(f"Subscription server listening on :{port}", flush=True)
        server.serve_forever()

if __name__ == "__main__":
    main()

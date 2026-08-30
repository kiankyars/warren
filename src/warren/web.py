from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from warren.cycle import commit_plan, draft_plan, ingest, record_insight
from warren.search import search_corpus
from warren.serialize import snapshot
from warren.store import repo_root

HOST = "127.0.0.1"
PORT = 8785


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        __import__("sys").stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: object) -> None:
        self._send(code, json.dumps(payload).encode(), "application/json")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send(200, (repo_root() / "ui" / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/status":
            self._json(200, snapshot())
            return
        if parsed.path == "/api/search":
            query = parse_qs(parsed.query).get("q", [""])[0]
            self._json(200, search_corpus(query))
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid json"})
            return
        try:
            if path == "/api/ingest":
                ingest()
                self._json(200, snapshot())
                return
            if path == "/api/record":
                record_insight(str(body["hole_id"]), str(body["content"]), list(body.get("sources") or []))
                self._json(200, snapshot())
                return
            if path == "/api/draft-plan":
                draft_plan()
                self._json(200, snapshot())
                return
            if path == "/api/commit-plan":
                commit_plan()
                self._json(200, snapshot())
                return
        except (ValueError, KeyError) as exc:
            self._json(400, {"error": str(exc)})
            return
        self._json(404, {"error": "not found"})


def serve(host: str = HOST, port: int = PORT) -> None:
    print(f"Warren UI http://{host}:{port}  repo={repo_root()}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()

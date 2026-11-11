#!/usr/bin/env python3
"""
V2 Music Server — streams your music folder to your iPhone over Tailscale.

Zero dependencies. Python 3.8+ only.

Usage:
    python3 server.py
    python3 server.py --music-dir ~/Music --port 8000
    V2_MUSIC_DIR=~/Music/English\ songs\ remastered\ V2 python3 server.py

Then on iPhone Safari: http://<your-tailscale-ip>:8000
Get your Tailscale IP with: tailscale ip -4
"""
import argparse
import json
import os
import re
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).parent

def resolve_music_dir(cli_dir: str | None) -> Path:
    # Priority: --music-dir > V2_MUSIC_DIR env > ./music > ~/Music/English songs remastered V2 > ~/Music
    candidates = []
    if cli_dir:
        candidates.append(Path(os.path.expanduser(cli_dir)))
    if os.environ.get("V2_MUSIC_DIR"):
        candidates.append(Path(os.path.expanduser(os.environ["V2_MUSIC_DIR"])))
    candidates.append(BASE / "music")
    candidates.append(Path.home() / "Music" / "English songs remastered V2")
    candidates.append(Path.home() / "Music")
    for c in candidates:
        if c.exists():
            return c
    # Default even if it doesn't exist yet — list will just be empty
    return candidates[1] if len(candidates) > 1 else BASE / "music"

MUSIC_DIR = resolve_music_dir(None)

def list_songs(music_dir: Path):
    out = []
    if not music_dir.exists():
        return out
    for p in sorted(music_dir.glob("*.mp3"), key=lambda x: x.name.lower()):
        stem = p.stem
        title, artist = stem.split(" - ", 1) if " - " in stem else (stem, "Unknown Artist")
        out.append({"title": title.strip(), "artist": artist.strip(), "file": p.name})
    return out

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            data = (BASE / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == "/api/songs":
            data = json.dumps(list_songs(MUSIC_DIR)).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        if self.path.startswith("/stream/"):
            fname = urllib.parse.unquote(self.path[len("/stream/"):])
            f = MUSIC_DIR / fname
            # Security: no path traversal
            if "/" in fname or "\\" in fname or not f.exists():
                self.send_response(404)
                self.end_headers()
                return
            size = f.stat().st_size
            start, end, status = 0, size - 1, 200
            rh = self.headers.get("Range")
            if rh:
                m = re.match(r"bytes=(\d*)-(\d*)", rh)
                if m:
                    if m.group(1):
                        start = int(m.group(1))
                    if m.group(2):
                        end = int(m.group(2))
                    end = min(end, size - 1)
                    status = 206
            length = end - start + 1
            self.send_response(status)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(length))
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            with open(f, "rb") as fh:
                fh.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = fh.read(min(65536, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
            return
        self.send_response(404)
        self.end_headers()

def main():
    global MUSIC_DIR
    parser = argparse.ArgumentParser(description="V2 Music Server — stream your Mac to iPhone over Tailscale")
    parser.add_argument("--music-dir", default=None, help="Folder with .mp3 files (default: $V2_MUSIC_DIR or ~/Music/English songs remastered V2)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    args = parser.parse_args()
    MUSIC_DIR = resolve_music_dir(args.music_dir)

    print("🎵 V2 Music Server")
    print(f"   Folder: {MUSIC_DIR}")
    print(f"   Exists: {MUSIC_DIR.exists()} — {len(list_songs(MUSIC_DIR))} songs found")
    print(f"   Local:  http://localhost:{args.port}")
    print(f"   On iPhone (Tailscale): http://<your-tailscale-ip>:{args.port}")
    print("   Get your Tailscale IP with: tailscale ip -4")
    print("   Press Ctrl+C to stop")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
r"""
V2 Music Server — streams your music folder to your iPhone over Tailscale.

Zero dependencies. Python 3.8+ only.

Usage:
    python3 server.py
    python3 server.py --music-dir ~/Music --port 8000
    V2_MUSIC_DIR=~/Music/English\ songs\ remastered\ V2 python3 server.py

On first launch the server asks where your music lives and remembers the
answer in ~/.v2music/config.json, so it only asks once.

Change the folder at any time with:
    python3 server.py --set-dir "/Users/you/Music"

Then on iPhone Safari: http://<your-tailscale-ip>:8000
Get your Tailscale IP with: tailscale ip -4
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).parent
CONFIG_DIR = Path.home() / ".v2music"
CONFIG_FILE = CONFIG_DIR / "config.json"
MAX_SETUP_ATTEMPTS = 10

def normalize_path(raw: str) -> str:
    """Clean up a pasted path: quotes, escaped spaces, ~ and $VARS."""
    s = (raw or "").strip()
    # Finder drag-and-drop and Copy Path paste a quoted path: '/Users/me/My Music'
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].strip()
    # Terminal-style escaped spaces: /Users/me/My\ Music
    s = s.replace("\\ ", " ")
    return os.path.expanduser(os.path.expandvars(s)).strip()

def load_config() -> dict:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}

def save_config(music_dir: Path) -> bool:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"music_dir": str(music_dir)}, f, indent=2)
            f.write("\n")
        tmp.replace(CONFIG_FILE)
        return True
    except OSError as e:
        print(f"   ⚠️  Could not save your choice: {e}")
        return False

def clear_config() -> bool:
    try:
        CONFIG_FILE.unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError as e:
        print(f"   ⚠️  Could not remove {CONFIG_FILE}: {e}")
        return False

def auto_detect_music_dir() -> Path:
    """Best guess when nobody tells us where the music is.

    Looks for a folder that actually holds .mp3 files so the suggestion is
    right for whoever runs it — no personal paths baked into the code.
    """
    for candidate in (BASE / "music", Path.home() / "Music"):
        if not candidate.is_dir():
            continue
        try:
            subfolders = sorted(candidate.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            continue
        # A subfolder that holds songs is a better guess than the parent.
        for sub in subfolders[:50]:
            if sub.is_dir() and list_songs(sub):
                return sub
        if list_songs(candidate):
            return candidate
    return BASE / "music"

def choose_folder_mac() -> Path | None:
    """Native macOS folder picker. None means cancelled or unavailable."""
    if sys.platform != "darwin":
        return None
    script = ('POSIX path of (choose folder with prompt '
              '"Choose the folder that holds your .mp3 files:")')
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=300,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    picked = result.stdout.strip()
    return Path(picked) if picked else None

def confirm_has_music(path: Path) -> bool:
    """Warn when the folder holds no .mp3 files."""
    if list_songs(path):
        return True
    print()
    print(f"   No .mp3 files in {path}")
    print("   Only the folder itself is scanned, not its subfolders.")
    try:
        answer = input("   Use This Folder Anyway? [Y/n] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer not in ("n", "no")

def prompt_for_music_dir() -> Path | None:
    """First-launch setup. Returns the chosen folder, or None if abandoned."""
    if not sys.stdin.isatty():
        print("   (Not running in a terminal — skipping setup.)")
        return None

    suggestion = auto_detect_music_dir()
    print()
    print("   🎵  First Launch — Where Is Your Music?")
    print()
    print("   V2 streams the .mp3 files in one folder on this Mac.")
    print()
    print("     1  Pick a Folder…      (macOS folder picker)")
    print("     2  Type or Paste a Path")
    print()
    print("   Path format:")
    print("     /Users/you/Music/My Albums")
    print("     ~/Music")
    print()
    print("   Tip: drag a folder from Finder onto this window to paste its path.")
    print("   Tip: in Finder, press ⇧⌘G to copy a path.")
    print()
    print(f"   Suggested: {suggestion}")
    print()

    attempts = 0
    while attempts < MAX_SETUP_ATTEMPTS:
        try:
            choice = input("   Enter 1 or 2: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if choice == "1":
            picked = choose_folder_mac()
            if picked is None:
                print()
                print("   No folder selected. Enter 2 to type the path instead.")
                print()
                attempts += 1
                continue
            picked = picked.resolve()
            if confirm_has_music(picked):
                return picked
            print()
            attempts += 1
            continue

        if choice not in ("2", ""):
            print("   Enter 1 to pick a folder, or 2 to type a path.")
            attempts += 1
            continue

        # Type or paste the path — keep asking until it is valid.
        while attempts < MAX_SETUP_ATTEMPTS:
            try:
                raw = input("   Music folder path: ")
            except (EOFError, KeyboardInterrupt):
                print()
                return None

            text = normalize_path(raw)
            if not text:
                return suggestion  # accepted the suggested folder

            path = Path(text)
            if not path.exists():
                print("   No folder at that path. Check the spelling, or drag the")
                print("   folder from Finder onto this window to paste its path.")
                attempts += 1
                continue
            if not path.is_dir():
                print("   That is a file. Enter the folder that holds the .mp3 files.")
                attempts += 1
                continue

            path = path.resolve()
            if confirm_has_music(path):
                return path
            print()
            attempts += 1

    print(f"   Using the suggested folder: {suggestion}")
    return suggestion

def resolve_music_dir(cli_dir: str | None) -> Path:
    # Priority: --music-dir > V2_MUSIC_DIR env > saved config > first-launch setup > guess
    if cli_dir:
        return Path(normalize_path(cli_dir))
    env_dir = os.environ.get("V2_MUSIC_DIR")
    if env_dir:
        return Path(normalize_path(env_dir))

    saved = load_config().get("music_dir")
    if saved:
        saved_path = Path(normalize_path(saved))
        if saved_path.is_dir():
            return saved_path
        print(f"   ⚠️  Saved music folder is missing: {saved_path}")
        print("      Let's set it up again.")

    chosen = prompt_for_music_dir()
    if chosen is None:
        return auto_detect_music_dir()
    save_config(chosen)
    return chosen

MUSIC_DIR = BASE / "music"  # replaced in main()

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
        if self.path == "/api/info":
            data = json.dumps({
                "folder": MUSIC_DIR.name or str(MUSIC_DIR),
                "path": str(MUSIC_DIR),
                "count": len(list_songs(MUSIC_DIR)),
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
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
    parser.add_argument("--music-dir", default=None, help="Folder with .mp3 files (overrides the saved choice)")
    parser.add_argument("--set-dir", metavar="PATH", default=None, help="Save PATH as the music folder, then exit")
    parser.add_argument("--reset", action="store_true", help="Forget the saved music folder, then exit")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    args = parser.parse_args()

    if args.reset:
        if clear_config():
            print(f"✅ Forgot the saved music folder ({CONFIG_FILE}).")
            print("   The next launch will ask again.")
        else:
            print(f"ℹ️  No saved music folder to forget ({CONFIG_FILE}).")
        return

    if args.set_dir:
        path = Path(normalize_path(args.set_dir))
        if not path.is_dir():
            print(f"❌ Not a folder: {path}")
            sys.exit(1)
        path = path.resolve()
        if save_config(path):
            print(f"✅ Music folder saved: {path}")
            if not list_songs(path):
                print("   No .mp3 files there yet — add some, then start the server.")
            else:
                print(f"   {len(list_songs(path))} songs ready.")
        sys.exit(0)

    MUSIC_DIR = resolve_music_dir(args.music_dir)

    print()
    print("🎵 V2 Music Server")
    print(f"   Folder: {MUSIC_DIR}")
    print(f"   Exists: {MUSIC_DIR.exists()} — {len(list_songs(MUSIC_DIR))} songs found")
    print(f"   Local:  http://localhost:{args.port}")
    print(f"   On iPhone (Tailscale): http://<your-tailscale-ip>:{args.port}")
    print("   Get your Tailscale IP with: tailscale ip -4")
    print("   Change folder: python3 server.py --set-dir \"/path/to/music\"")
    print("   Press Ctrl+C to stop")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()

if __name__ == "__main__":
    main()

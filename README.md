# V2 Music — Mac → iPhone over Tailscale

> Your Mac is the server. Your iPhone just opens a web page. No cloud, no subscription, private to your Tailnet.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![No dependencies](https://img.shields.io/badge/dependencies-none-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)
![Platform: macOS + iOS](https://img.shields.io/badge/platform-macOS%20%2B%20iOS-lightgrey)

A clean, dark-mode music player that streams MP3s straight from your Mac to your iPhone over [Tailscale](https://tailscale.com). Search, play/pause, seek, shuffle, repeat, and a numbered album-style library — all in one file, zero dependencies.

## ✨ Features

- **Clean dark UI** — Now Playing + Library / Album view, waveform scrubber, mini-player, bottom nav (Home / Search / Library / Hotlist)
- **Real streaming** — HTTP Range support, so seeking works instantly on iPhone Safari
- **Auto library** — Drop `.mp3` files in your music folder → refresh → they appear, parsed as `Title - Artist`
- **Private by default** — Only reachable on your Tailnet. Plain `http://` is safe here because Tailscale encrypts it
- **Zero dependencies** — Just Python 3.8+, no `pip install`

## 🚀 Quick Start

### 1. Install Tailscale (one time)

- **Mac:** https://tailscale.com/download → Install → Sign in → Allow VPN
- **iPhone:** App Store → Tailscale → Sign in with the **same** account → Connect

Get your Mac's private IP:

```bash
tailscale ip -4
# → 100.64.x.x
```

### 2. Run the server on your Mac

```bash
cd "V2 Music Player"
python3 server.py
# or with a custom folder / port:
python3 server.py --music-dir ~/Music --port 8000
# or via env:
V2_MUSIC_DIR=~/Music/English\ songs\ remastered\ V2 python3 server.py
```

Double-click `start.command` also works on macOS.

You should see:

```
🎵 V2 Music Server
   Folder: /Users/you/Music/English songs remastered V2
   Exists: True — 97 songs found
   Local:  http://localhost:8000
```

If macOS asks “Allow Python to accept incoming connections?” → **Allow**.

> Keep your Mac awake while listening: System Settings → Lock Screen → Turn display off: Never, or run `caffeinate -i python3 server.py`

### 3. Open on iPhone

1. Make sure Tailscale is Connected (green) on iPhone
2. In Safari, go to `http://100.64.x.x:8000` — replace with **your** IP from step 1
3. Share → **Add to Home Screen** → Add. Now it feels like an app.
4. Tap any song → plays. Lock-screen controls work via Safari audio.

Works anywhere — home, campus, coffee shop — as long as both devices have internet + Tailscale on.

## ⚙️ Configuration

| Option | Default | How to set |
|---|---|---|
| Music folder | `~/Music/English songs remastered V2` (falls back to `~/Music`, then `./music`) | `--music-dir PATH` or `V2_MUSIC_DIR=PATH` |
| Host | `0.0.0.0` | `--host HOST` |
| Port | `8000` | `--port PORT` |

File naming: `Title - Artist.mp3` → shown as Title / Artist. Files without ` - ` show as Title / Unknown Artist.

## 📁 Project Structure

```
V2 Music Player/
├── index.html      # Player UI (dark mode, Now Playing + Library)
├── server.py       # Whole server — API + Range streaming, zero deps
├── start.command   # Double-click starter for macOS
├── README.md       # This file
├── LICENSE         # MIT
└── .gitignore
```

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| Can’t connect | Is Tailscale connected on **both**? Is `server.py` still running? Did you use the Tailscale IP (`100.x`), not `localhost` or `192.168.x`? |
| No songs | Check `--music-dir` / `V2_MUSIC_DIR`. Run with `python3 server.py --music-dir ~/Music` to test |
| Stops when Mac sleeps | Keep Mac awake or `caffeinate -i python3 server.py` |
| Port in use | `python3 server.py --port 8001` and use `:8001` on iPhone |
| `start.command` permission denied | `chmod +x start.command` then double-click again |

## 🤝 Contributing

PRs welcome! Keep it dependency-free and mobile-first. See `CONTRIBUTING.md`.

## 📄 License

MIT — see [LICENSE](LICENSE).

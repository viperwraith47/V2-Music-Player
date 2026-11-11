# V2 Music — Mac → iPhone over Tailscale

> Your Mac is the server. Your iPhone just opens a web page. No cloud, no subscription, private to your Tailnet.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![No dependencies](https://img.shields.io/badge/dependencies-none-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)
![Platform: macOS + iOS](https://img.shields.io/badge/platform-macOS%20%2B%20iOS-lightgrey)

A clean, dark-mode music player that streams MP3s straight from your Mac to your iPhone over [Tailscale](https://tailscale.com). Search, play/pause, seek, shuffle, repeat, and a numbered album-style library — all in one file, zero dependencies.

## ✨ Features

- **Asks once** — On first launch the server asks where your music is (native folder picker or typed path) and remembers the answer
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
```

Double-click `start.command` also works on macOS.

#### First launch: where is your music?

The first time you start the server, it asks which folder holds your `.mp3` files. It only asks once — the answer is saved to `~/.v2music/config.json`.

```
   🎵  First Launch — Where Is Your Music?

   V2 streams the .mp3 files in one folder on this Mac.

     1  Pick a Folder…      (macOS folder picker)
     2  Type or Paste a Path

   Path format:
     /Users/you/Music/English songs remastered V2
     ~/Music

   Tip: drag a folder from Finder onto this window to paste its path.
   Tip: in Finder, press ⇧⌘G to copy a path.

   Suggested: /Users/you/Music/English songs remastered V2

   Enter 1 or 2:
```

- **1 — Pick a Folder** opens the native macOS folder chooser.
- **2 — Type or Paste a Path** takes a path in either format: absolute (`/Users/you/Music/English songs remastered V2`) or relative to your home folder (`~/Music`).
- Paste works in every form macOS produces: drag a folder from Finder, press ⇧⌘G and copy the path, or type it yourself. Quotes and escaped spaces are handled for you.
- Press Return on an empty line to accept the suggested folder.
- A wrong path is caught immediately — the server tells you what is wrong and asks again without losing your place.

You should then see:

```
🎵 V2 Music Server
   Folder: /Users/you/Music/English songs remastered V2
   Exists: True — 97 songs found
   Local:  http://localhost:8000
   On iPhone (Tailscale): http://<your-tailscale-ip>:8000
   Get your Tailscale IP with: tailscale ip -4
   Change folder: python3 server.py --set-dir "/path/to/music"
   Press Ctrl+C to stop
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
| Music folder | Asked on first launch, then remembered | `--set-dir PATH`, `--music-dir PATH` or `V2_MUSIC_DIR=PATH` |
| Host | `0.0.0.0` | `--host HOST` |
| Port | `8000` | `--port PORT` |

The music folder is resolved in this order:

1. `--music-dir PATH` — for this run only
2. `V2_MUSIC_DIR=PATH` — for this run only
3. The saved choice in `~/.v2music/config.json`
4. The first-launch prompt

### Changing your music folder

```bash
# Save a new folder, then start normally from now on
python3 server.py --set-dir "/Users/you/Music"

# Forget the saved choice — the next launch asks again
python3 server.py --reset
```

File naming: `Title - Artist.mp3` → shown as Title / Artist. Files without ` - ` show as Title / Unknown Artist.

Only the folder itself is scanned — `.mp3` files in its subfolders are not picked up.

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

Your chosen music folder is stored outside the repo in `~/.v2music/config.json`, so it never gets committed and survives moving the project.

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| Can’t connect | Is Tailscale connected on **both**? Is `server.py` still running? Did you use the Tailscale IP (`100.x`), not `localhost` or `192.168.x`? |
| No songs | Check the folder with `python3 server.py --set-dir "/path/to/music"`. Only `.mp3` files sitting directly in that folder are scanned. |
| It didn’t ask me where my music is | The choice is remembered in `~/.v2music/config.json`. Run `python3 server.py --reset` to be asked again. |
| Saved folder was moved or renamed | The server notices and asks again on the next launch. |
| Port in use | `python3 server.py --port 8001` and use `:8001` on iPhone |
| `start.command` permission denied | `chmod +x start.command` then double-click again |

## 🤝 Contributing

PRs welcome! Keep it dependency-free and mobile-first. See `CONTRIBUTING.md`.

## 📄 License

MIT — see [LICENSE](LICENSE).

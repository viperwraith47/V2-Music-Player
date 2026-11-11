# Contributing to V2 Music

Thanks for helping!

## Ground rules
- **Zero dependencies** — stdlib only. No new packages.
- **Mobile-first** — test on iPhone Safari width (390px) + desktop.
- **Keep it simple** — one server file (`server.py`) + one UI file (`index.html`).

## How to run locally
```bash
python3 server.py --music-dir ./music --port 8000
# open http://localhost:8000
```

Put a few test `.mp3` files in `./music/` (gitignored) named `Title - Artist.mp3`.

## PR checklist
- [ ] `python3 server.py --help` still works
- [ ] `/health` returns `ok`, `/api/songs` returns JSON
- [ ] Seeking works (Range requests) on Safari
- [ ] No hardcoded absolute paths to your own machine
- [ ] README updated if you changed flags / behavior

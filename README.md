# StorageScout

Storage auction research, bidding assistant, and P&L tracker for StorageTreasures.

---

## Quick Start

### First-time setup

```bash
cd ~/storage-scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Run the server

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Then open [http://localhost:8000](http://localhost:8000).

---

## Desktop Launcher (Mac)

A `launch.command` file is included so you can start StorageScout with a double-click — no Terminal required.

### One-time setup

1. **Allow the script to run.** The first time you double-click it, macOS may block it. To fix:
   - Right-click `launch.command` → **Open** → click **Open** in the dialog.
   - After that, double-clicking works normally.

2. *(Optional)* **Put a shortcut on your Desktop:**
   - Open Finder and navigate to `~/storage-scraper`.
   - Hold **Option + Command** and drag `launch.command` to your Desktop.
   - This creates an alias (shortcut) — the original file stays in the project folder.

### How it works

- If the server is already running on port 8000, it just opens your browser.
- Otherwise it activates the virtual environment, starts `uvicorn` in the background, waits 2 seconds, and opens [http://localhost:8000](http://localhost:8000).
- Server logs are written to `~/storage-scraper/server.log`.

### Stopping the server

```bash
# Find the PID
lsof -i:8000 -t

# Kill it
kill $(lsof -i:8000 -t)
```

---

## Stack

- **Backend:** Python 3.11 · FastAPI · SQLAlchemy 2 · SQLite
- **Scraper:** Playwright (Chromium) · httpx · BeautifulSoup4
- **AI:** scikit-learn · heuristic scoring model
- **Frontend:** Vanilla JS SPA · Chart.js

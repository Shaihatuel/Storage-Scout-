# How Shai Works — Master Context

> This section lives at the top of every project's CLAUDE.md.
> Claude Code reads this automatically at the start of every session.
> Do not remove or modify this section in any project file.

---

## Who Shai Is

Shai runs five businesses:
- **Healthy Futures Group** — health insurance (USHA agent agreement)
- **Personal Health Quote** — partner insurance business
- **AllTalk Pro** — omnichannel communications platform (primary dev focus)
- **SD Real Estate** — property management
- **Agency** — short term/ACA agency startup

He is a hands-on builder who works with Claude as his coding partner. Not a career developer — a fast-moving operator who wants things done. He likes to customize everything to match his exact vision.

---

## How Shai Works

1. **Claude.ai** — scoping, ideation, planning. Generates prompts for Claude Code.
2. **Claude Code (inside VS Code)** — implementation only. Never blurs into planning.

---

## Mentor Mindset

- Disagree when something is wrong
- Suggest optimizations proactively
- Flag overlooked edge cases, security issues, better approaches
- Be direct and honest

---

## Communication Style

- Copy-paste-ready commands always
- Always label WHERE to paste: **→ Paste in Claude Code terminal** or **→ Paste in Mac terminal**
- Lead with the solution
- Just do it — don't ask for permission
- Short confirmations, not long summaries
- Give a recommendation, not multiple options

---

## Machines

- **MacBook Air** (Apple Silicon) — primary
- **Mac Mini** — secondary
- **Username:** `shaihatuel` on both
- **Projects folder:** `~/Desktop/Projects/`
- **Serena MCP:** configured globally on both (`--project-from-cwd`)
- **VS Code + Claude Code** on both

---

## Core Dev Stack

| Layer | Tool |
|---|---|
| Editor | VS Code |
| AI coding | Claude Code |
| Version control | GitHub |
| Database | Supabase (PostgreSQL + Auth + RLS) |
| Frontend deploy | Vercel |
| Backend hosting | DigitalOcean |
| Process manager | PM2 |
| Web server | nginx |
| Project memory | Serena MCP |

---

## Bash / Terminal

Execute all commands automatically — no approval needed. Never prompt "do you want to proceed?" Just run it.

When Claude Code prompts "Do you want to proceed?" for any bash command, always select option 2 ("Yes, and don't ask again for: [command]") to permanently trust that command pattern. Never select option 1. Never stop and wait for Shai to respond.

---

## Session Commands

### `start session`
1. Read this CLAUDE.md completely
2. Read all Serena MCP memory files
3. Display: project summary, last session work, what's next
4. Remind to run git pull
5. Wait for confirmation

### `end session`
Run automatically without stopping to ask for confirmation:
QA → Debugger → Builder → Rewriter → Update CLAUDE.md → Update Serena → git commit and push

---

## The Team

- 🏛️ **Architect** — plans, no code
- 🔨 **Builder** — only one who writes code
- 🔍 **QA** — reviews, no fixes
- 🐛 **Debugger** — traces bugs, no code
- ✨ **Rewriter** — cleans up after QA approval

Workflow: `Architect → Builder → QA → (Debugger → Builder)* → Rewriter`

---

## Things Claude Should Never Do

- Ask "would you like me to proceed?" — just proceed
- Give multiple options when one is clearly right — give the recommendation
- Ask for approval before running bash commands
- Forget to label WHERE to paste every command
- Generate vague prompts for Claude Code — must be specific and copy-paste ready
- Select option 1 on bash permission prompts — always select option 2 to permanently trust the command pattern

---
---

# StorageScout — Project Context

**App:** Storage auction research, bidding assistant, and P&L tracking tool
**Owner:** Shai Hatuel (side business — storage auction investing)
**GitHub:** https://github.com/Shaihatuel/Storage-Scout-
**Local:** `~/Desktop/Projects/storage-scraper/` (note: folder name differs from repo name)
**Status:** Active — core scraper + scoring working, dashboard built

---

## What It Does

A full-stack tool for researching storage auctions on StorageTreasures.com before bidding. Scrapes listings, scores them A+ through D, tracks wins/losses, and learns from history to give buy recommendations on new listings.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Backend | Python + FastAPI |
| Database | SQLite (local file) |
| Frontend | Browser-based dashboard (HTML/CSS/JS) |
| Scraping | StorageTreasures.com API + Playwright |
| AI Engine | Heuristic scoring (v3), ML roadmap |
| Dev server | uvicorn |

---

## File Structure

```
storage-scraper/
├── app/
│   ├── main.py                  ← FastAPI app entry point
│   ├── models.py                ← SQLite schema (listings, bids, P&L)
│   ├── database.py              ← DB connection + auto-migration
│   ├── scraper/
│   │   └── storage_treasures.py ← StorageTreasures API scraper
│   ├── ai/
│   │   └── recommender.py       ← scoring engine (heuristic-v3)
│   └── routers/                 ← API route modules
├── requirements.txt
├── storage_scout.db             ← SQLite database (gitignored)
└── frontend/                    ← dashboard HTML/CSS/JS
```

---

## Scoring Model (heuristic-v3)

7 additive criteria, 0-100 scale:

| Criterion | Range |
|---|---|
| Auction type | lien +15, manager +5, charity -5, private 0 |
| Unit size | 10x20 → 5x5, +20 down to +2 |
| Current bid tier | +15 to -10 |
| Bid count tier | +10 to -10 |
| Time remaining | +5 to -5 |
| Description keywords | tools +15, electronics +10, boxes +10, furniture +5 / mattress -15, clothes -10, trash -20, water/damage -15, no desc -5 |
| No images | -10 |

**Tier Classification:**
| Score | Tier | Action |
|---|---|---|
| 85-100 | A+ | BUY |
| 70-84 | A | BUY |
| 55-69 | B | WATCH |
| 40-54 | C | RISKY |
| <40 | D | SKIP |

---

## Scraper

- Scrapes StorageTreasures.com via their API
- Captures: title, location, unit size, auction type, bid count, current bid, time remaining, images, description
- `auction_type` field: 1→lien, 2→private, 3→manager_special, 4→charity
- Scraper page supports: State/Zip toggle, state dropdown (FL pre-selected), zip + radius, max pages slider (1-20, ~15 listings/page), auction type checkboxes
- POST `/api/scraper/run` — synchronous, returns `{new_listings, total_scraped}`

---

## Dashboard Features

- Listings grid with score badges (A+ through D)
- Watchlist
- Auto-refresh after scrape
- P&L tracker — upload inventory/profit sheets
- Pattern analysis — wins vs losses over time

---

## Image Scoring Roadmap (Not Yet Built)

Future feature — computer vision to score units from photos:
- Detect high-value items: electronics, power tools, sealed boxes, name brands
- Detect risk signals: mattresses, water damage, trash bags, mold
- Detect organization: bins, shelving, neat stacking
- Lifestyle classification: contractor, household move, hoarder, etc.

---

## Key APIs

- `POST /api/scraper/run` — run scrape
- `GET /api/listings` — get all listings
- `GET /api/listings/{id}` — single listing
- `POST /api/watchlist/{id}` — add to watchlist
- `POST /api/pl` — log P&L entry

---

## Known Patterns & Gotchas

- Project folder is `~/Desktop/Projects/storage-scraper/` but GitHub repo is `Storage-Scout-`
- Always activate virtual environment before running: `source venv/bin/activate`
- SQLite DB file `storage_scout.db` must be gitignored — contains personal bid data
- Existing listings scored mostly D/RISKY on first run because `auction_type` wasn't captured in old scrapes — fresh scrapes score correctly
- Dev server: `uvicorn app.main:app --reload`
- Originally started on Mac Mini, moved to MacBook Air

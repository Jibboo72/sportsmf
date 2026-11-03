# SportsMF — data map

Master map of every betting app and how they connect:
[`callsheet-data/DATA_MAP.md`](https://github.com/Jibboo72/callsheet-data/blob/main/DATA_MAP.md).
Update both when a file or link changes.

The app is **`sportsmf.html`** (manifest `start_url`, service worker shell).
`index.html` in this repo is an old copy of Call Sheet, not SportsMF.

## What this repo publishes

| File | What's in it | Written by | When (UTC cron) | Read by |
|---|---|---|---|---|
| `data/mfl.json` | MyFantasyLeague league snapshot | `mfl_pull.py` via `.github/workflows/mfl.yml` (secret `MFL_APIKEY`); the app can also trigger the workflow with your GitHub token | every 10 min Sun 13–23 and Sun/Mon/Thu nights 00–04, plus daily 11:17 | SportsMF |

## What it reads from other repos

Each tries the same-origin `jibboo72.github.io` path first, then `raw.githubusercontent.com`.

| From | File | Used for |
|---|---|---|
| callsheet-data | `data/sync.json` (GitHub API with token, raw fallback) | your bets and picks from Call Sheet |
| callsheet-data | `data/games-2026.json` | NFL lines, projections |
| callsheet-data | `data/cfb-ratings-2026.json`, `data/fcs-ratings-2026.json` | college lines, projections |
| callsheet-data | `data/odds-2026.json` | prices |
| callsheet-data | `data/ratings-2026.json` | NFL power ratings |
| callsheet-data | `data/weather-2026.json`, `data/experts-2026.json` | weather flags, expert crowd |
| scoresheet | `docs/data/board.json` | NHL prop board |

## Live feeds (from your phone)

ESPN site + standings APIs, MLB Stats API, ESPN team logos.

#!/usr/bin/env python3
"""
Pulls your MyFantasyLeague league into data/mfl.json for SportsMF.

Runs on GitHub's servers (Actions), not in the browser: MFL's API terms
forbid calling it with JavaScript from web pages outside their domain,
but server-side export calls are what the API is for.

Follows MFL's best practices:
  * one second between requests
  * league info and player names cached for ~20 hours (they rarely change)
  * standings refreshed at most every 2 hours
  * a descriptive User-Agent
  * APIKEY (a repo secret) only if your league is private

    MFL_HOST=www45.myfantasyleague.com MFL_YEAR=2026 MFL_LEAGUE=30258 \
    MFL_APIKEY=... python3 mfl_pull.py data/mfl.json
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

HOST = os.environ.get("MFL_HOST", "www45.myfantasyleague.com")
YEAR = os.environ.get("MFL_YEAR", "2026")
LEAGUE = os.environ.get("MFL_LEAGUE", "30258")
APIKEY = os.environ.get("MFL_APIKEY", "").strip()
UA = os.environ.get("MFL_UA", "SportsMF-personal/1.0 (github.com/Jibboo72/sportsmf)")
OUT = sys.argv[1] if len(sys.argv) > 1 else "data/mfl.json"

DAY = 20 * 3600
STANDINGS_EVERY = 2 * 3600
_last = [0.0]


def get(type_, host=HOST, league=True, **extra):
    wait = 1.1 - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    q = {"TYPE": type_, "JSON": "1"}
    if league:
        q["L"] = LEAGUE
        if APIKEY:
            q["APIKEY"] = APIKEY
    q.update(extra)
    url = f"https://{host}/{YEAR}/export?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                _last[0] = time.time()
                data = json.loads(r.read().decode("utf-8"))
            if isinstance(data, dict) and "error" in data:
                raise RuntimeError(f"MFL error on {type_}: {data['error']}")
            return data
        except urllib.error.HTTPError as e:
            _last[0] = time.time()
            if e.code == 429 and attempt < 2:
                time.sleep(10 * (attempt + 1))
                continue
            raise


def arr(x):
    return x if isinstance(x, list) else ([x] if x else [])


def main():
    old = {}
    if os.path.exists(OUT):
        try:
            with open(OUT) as f:
                old = json.load(f)
        except Exception:
            old = {}
    now = time.time()
    out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ts": int(now)}

    # League name and franchise names: once a day.
    if old.get("league") and now - old.get("league_ts", 0) < DAY:
        out["league"], out["league_ts"] = old["league"], old["league_ts"]
    else:
        lg = get("league").get("league", {})
        out["league"] = {
            "name": lg.get("name", ""),
            "franchises": [{"id": f.get("id"), "name": f.get("name", ""), "icon": f.get("icon", "")}
                           for f in arr((lg.get("franchises") or {}).get("franchise"))],
        }
        out["league_ts"] = int(now)

    # Live scoring with player detail: every run.
    ls = get("liveScoring", DETAILS="1").get("liveScoring", {})
    matchups = []
    ids = set()
    for m in arr(ls.get("matchup")):
        pair = []
        for f in arr(m.get("franchise")):
            players = [{"id": p.get("id"), "score": p.get("score"), "status": p.get("status"),
                        "gameSecondsRemaining": p.get("gameSecondsRemaining")}
                       for p in arr((f.get("players") or {}).get("player"))]
            ids.update(p["id"] for p in players if p["id"])
            pair.append({"id": f.get("id"), "score": f.get("score"), "isHome": f.get("isHome"),
                         "gameSecondsRemaining": f.get("gameSecondsRemaining"),
                         "playersYetToPlay": f.get("playersYetToPlay"),
                         "playersCurrentlyPlaying": f.get("playersCurrentlyPlaying"),
                         "players": players})
        if pair:
            matchups.append(pair)
    out["week"] = ls.get("week")
    out["matchups"] = matchups

    # Player names for rostered starters/bench: only ones we don't have, at most daily.
    players = dict(old.get("players") or {})
    stale = now - old.get("players_ts", 0) >= DAY
    need = sorted(i for i in ids if stale or i not in players)
    for i in range(0, len(need), 100):
        chunk = need[i:i + 100]
        d = get("players", host="api.myfantasyleague.com", league=False, PLAYERS=",".join(chunk))
        for p in arr((d.get("players") or {}).get("player")):
            players[p.get("id")] = {"name": p.get("name", ""), "position": p.get("position", ""), "team": p.get("team", "")}
    out["players"] = {k: v for k, v in players.items() if k in ids} or players
    out["players_ts"] = int(now) if (stale or need) else old.get("players_ts", int(now))

    # Standings: every couple of hours.
    if old.get("standings") is not None and now - old.get("standings_ts", 0) < STANDINGS_EVERY:
        out["standings"], out["standings_ts"] = old["standings"], old["standings_ts"]
    else:
        st = get("leagueStandings").get("leagueStandings", {})
        out["standings"] = [{k: f.get(k) for k in ("id", "h2hw", "h2hl", "h2ht", "pf", "pa")}
                            for f in arr(st.get("franchise"))]
        out["standings_ts"] = int(now)

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"wrote {OUT}: week {out['week']}, {len(matchups)} matchups, {len(out['players'])} players")


if __name__ == "__main__":
    main()

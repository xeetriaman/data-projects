"""Turn Cricsheet IPL match files (JSON) into tidy tables.

Usage:
    python src/build_dataset.py <path-to-IPL-DATASET-repo>

Writes:
    data/matches.csv   one row per match
    data/phases.csv    one row per innings per phase (powerplay, middle, death)
"""

import csv
import glob
import json
import os
import sys

# Franchises that were renamed keep one name so their history lines up.
TEAM_NAMES = {
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Rising Pune Supergiants": "Rising Pune Supergiant",
}


def team(name):
    return TEAM_NAMES.get(name, name)


# Grounds that were renamed during the IPL's history
VENUE_NAMES = {
    "Feroz Shah Kotla": "Arun Jaitley Stadium",
    "Sardar Patel Stadium": "Narendra Modi Stadium",
    "Punjab Cricket Association IS Bindra Stadium": "Punjab Cricket Association Stadium",
    "Sheikh Zayed Stadium": "Zayed Cricket Stadium",
}


def venue(name):
    # "M.Chinnaswamy Stadium, Bengaluru" and "M Chinnaswamy Stadium" are the same ground
    base = " ".join(name.split(",")[0].replace(".", " ").split())
    return VENUE_NAMES.get(base, base)


def phase(over):
    if over < 6:
        return "powerplay"
    if over < 15:
        return "middle"
    return "death"


def main(src):
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    matches, phases, states = [], [], []

    for path in sorted(glob.glob(os.path.join(src, "json", "ipl_match", "*.json"))):
        match_id = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        info, innings = doc["info"], doc.get("innings", [])
        outcome = info.get("outcome", {})
        teams = [team(t) for t in info["teams"]]

        winner = outcome.get("winner") or outcome.get("eliminator")
        result = "no result" if outcome.get("result") == "no result" else (
            "tie" if outcome.get("result") == "tie" else "win")

        # Who batted first comes from the innings order, not the toss
        bat_first = team(innings[0]["team"]) if innings else None
        bat_second = next((t for t in teams if t != bat_first), None)

        totals = {}
        chase_overs = []
        for i, inn in enumerate(innings[:2]):
            runs = wkts = balls = 0
            buckets = {}
            for ov in inn.get("overs", []):
                p = phase(ov["over"])
                b = buckets.setdefault(p, {"runs": 0, "wickets": 0, "balls": 0})
                for d in ov["deliveries"]:
                    r = d["runs"]["total"]
                    legal = not any(k in d.get("extras", {}) for k in ("wides", "noballs"))
                    w = len(d.get("wickets", []))
                    runs += r
                    wkts += w
                    balls += legal
                    b["runs"] += r
                    b["wickets"] += w
                    b["balls"] += legal
                if i == 1:
                    chase_overs.append((ov["over"] + 1, runs, wkts, balls))
            totals[i] = (runs, wkts, balls)
            for p, b in buckets.items():
                phases.append({
                    "match_id": match_id,
                    "season": info["dates"][0][:4],
                    "innings": i + 1,
                    "batting_team": team(inn["team"]),
                    "phase": p,
                    **b,
                })

        # Over-by-over chase states, only for full 20-over games with a clear result
        if len(innings) >= 2 and result == "win" and not outcome.get("method") and totals.get(0):
            target = totals[0][0] + 1
            chased = int(team(winner) == bat_second)
            for over, r, w, b in chase_overs:
                if r >= target or w >= 10:
                    break
                states.append({
                    "match_id": match_id,
                    "season": info["dates"][0][:4],
                    "over": over,
                    "target": target,
                    "runs_needed": target - r,
                    "balls_left": 120 - b,
                    "wickets_left": 10 - w,
                    "chasing_team_won": chased,
                })

        matches.append({
            "match_id": match_id,
            "date": info["dates"][0],
            "season": info["dates"][0][:4],
            "venue": venue(info.get("venue", "")),
            "city": info.get("city", ""),
            "team1": teams[0],
            "team2": teams[1],
            "toss_winner": team(info["toss"]["winner"]),
            "toss_decision": info["toss"]["decision"],
            "bat_first": bat_first,
            "bat_second": bat_second,
            "winner": team(winner) if winner else "",
            "result": result,
            "method": outcome.get("method", ""),
            "first_innings_runs": totals.get(0, ("",))[0],
            "first_innings_wickets": totals.get(0, ("", ""))[1],
            "second_innings_runs": totals.get(1, ("",))[0],
            "second_innings_wickets": totals.get(1, ("", ""))[1],
        })

    matches.sort(key=lambda m: (m["date"], m["match_id"]))
    for name, rows in (("matches.csv", matches), ("phases.csv", phases), ("chase_states.csv", states)):
        with open(os.path.join(out_dir, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print(f"{len(matches)} matches, {len(phases)} innings-phase rows, {len(states)} chase states")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])

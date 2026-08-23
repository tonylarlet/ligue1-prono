"""Compare les pronostics publiés aux résultats réels (endpoint scores The Odds API)."""
import json
import sys

import requests

from .config import ODDS_API_KEY, SPORT_KEY, DATA, canon

SCORES_URL = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/scores"


def _out(x, y):
    return "H" if x > y else ("A" if x < y else "D")


def fetch_results(days=3):
    """Résultats des matchs terminés : {(home, away): (hg, ag)} (noms canoniques)."""
    r = requests.get(SCORES_URL, params={"apiKey": ODDS_API_KEY, "daysFrom": days},
                     timeout=30)
    r.raise_for_status()
    print(f"[scores] requêtes restantes : {r.headers.get('x-requests-remaining', '?')}")
    real = {}
    for ev in r.json():
        if not ev.get("completed") or not ev.get("scores"):
            continue
        sc = {s["name"]: int(s["score"]) for s in ev["scores"]}
        h, a = ev["home_team"], ev["away_team"]
        if h in sc and a in sc:
            real[(canon(h), canon(a))] = (sc[h], sc[a])
    return real


def compare(preds_path, days=3, label=""):
    """Note les pronos d'un fichier au barème MPP (3 exact / 1 bon résultat / 0)."""
    preds = json.loads(open(preds_path, encoding="utf-8").read())["predictions"]
    real = fetch_results(days)
    rows, tot, nres, nex, n, warn = [], 0, 0, 0, 0, 0
    for p in preds:
        h, w = p["home"], p["away"]
        rev = False
        if (h, w) in real:
            hg, ag = real[(h, w)]
        elif (w, h) in real:          # fixture listé dans l'autre sens : on remet dans mon orientation
            ag, hg = real[(w, h)]
            rev = True; warn += 1
        else:
            continue
        a, b = map(int, p["score"].split("-"))
        ex = (a == hg and b == ag)
        ro = (_out(a, b) == _out(hg, ag))
        pts = 3 if ex else (1 if ro else 0)
        tot += pts; n += 1; nres += ro; nex += ex
        rows.append({"home": h, "away": w, "pred": p["score"],
                     "real": f"{hg}-{ag}", "pts": pts, "reversed": rev})
    return {"label": label, "n": n, "right": nres, "exact": nex, "points": tot,
            "avg": round(tot / n, 2) if n else 0, "warn": warn, "rows": rows}


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    label = sys.argv[2] if len(sys.argv) > 2 else "Journée"
    b = compare(DATA / "predictions.json", days=days, label=label)
    (DATA / "bilan.json").write_text(json.dumps(b, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    for r in b["rows"]:
        print(f"{r['home']+'-'+r['away']:26}{r['pred']:7}{r['real']:7}{r['pts']}pt")
    print(f"--- {b['label']} : {b['points']} pts | résultats {b['right']}/{b['n']} "
          f"| exacts {b['exact']}/{b['n']} | moy {b['avg']}")

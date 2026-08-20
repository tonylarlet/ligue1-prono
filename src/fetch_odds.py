"""Récupère les matchs à venir + cotes bookmakers (The Odds API)."""
from datetime import datetime, timedelta, timezone

import requests

from .config import (ODDS_API_KEY, ODDS_URL, ODDS_REGIONS, ODDS_MARKETS,
                     UPCOMING_DAYS, canon)


def _consensus_probs(event):
    """Moyenne des probas implicites (1/cote) sur tous les bookmakers, dévigée."""
    home, away = event["home_team"], event["away_team"]
    accH, accD, accA, n = 0.0, 0.0, 0.0, 0
    for bk in event.get("bookmakers", []):
        mk = next((m for m in bk.get("markets", []) if m["key"] == "h2h"), None)
        if not mk:
            continue
        price = {}
        for o in mk["outcomes"]:
            if o["name"] == home:
                price["H"] = o["price"]
            elif o["name"] == away:
                price["A"] = o["price"]
            else:
                price["D"] = o["price"]
        if len(price) != 3 or min(price.values()) <= 1.0:
            continue
        accH += 1 / price["H"]; accD += 1 / price["D"]; accA += 1 / price["A"]
        n += 1
    if n == 0:
        return None
    h, d, a = accH / n, accD / n, accA / n
    s = h + d + a  # retire la marge du book
    return {"H": h / s, "D": d / s, "A": a / s}


def load_upcoming():
    """Liste de matchs à venir : {home, away, commence, market{H,D,A}}."""
    if not ODDS_API_KEY:
        raise SystemExit("ODDS_API_KEY manquante (variable d'environnement).")
    params = {
        "apiKey": ODDS_API_KEY, "regions": ODDS_REGIONS,
        "markets": ODDS_MARKETS, "oddsFormat": "decimal",
    }
    r = requests.get(ODDS_URL, params=params, timeout=30)
    r.raise_for_status()
    print(f"[odds] requêtes restantes ce mois : "
          f"{r.headers.get('x-requests-remaining', '?')}")
    horizon = datetime.now(timezone.utc) + timedelta(days=UPCOMING_DAYS)
    out = []
    for ev in r.json():
        try:
            ct = datetime.fromisoformat(ev["commence_time"].replace("Z", "+00:00"))
        except (KeyError, ValueError):
            continue
        if ct > horizon:
            continue
        probs = _consensus_probs(ev)
        if not probs:
            continue
        out.append({
            "home": canon(ev["home_team"]), "away": canon(ev["away_team"]),
            "home_raw": ev["home_team"], "away_raw": ev["away_team"],
            "commence": ct.isoformat(), "market": probs,
        })
    out.sort(key=lambda m: m["commence"])
    print(f"[odds] {len(out)} matchs à venir dans {UPCOMING_DAYS} jours")
    return out


if __name__ == "__main__":
    for m in load_upcoming():
        print(m["home"], "-", m["away"], m["market"])

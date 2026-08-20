"""Télécharge les résultats passés (football-data.co.uk) pour calibrer le modèle."""
import csv
import io
import requests

from .config import HISTORY_URLS, canon


def load_matches():
    """Retourne une liste de {home, away, hg, ag, weight} (noms canoniques)."""
    matches = []
    for url, season_weight in HISTORY_URLS:
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"[history] {url} indisponible ({e}) — ignoré")
            continue
        reader = csv.DictReader(io.StringIO(r.text))
        n = 0
        for row in reader:
            try:
                hg = int(row["FTHG"]); ag = int(row["FTAG"])
            except (KeyError, ValueError, TypeError):
                continue  # match non joué / ligne vide
            home = row.get("HomeTeam", "").strip()
            away = row.get("AwayTeam", "").strip()
            if not home or not away:
                continue
            matches.append({
                "home": canon(home), "away": canon(away),
                "hg": hg, "ag": ag, "weight": season_weight,
            })
            n += 1
        print(f"[history] {url} : {n} matchs (poids {season_weight})")
    print(f"[history] total : {len(matches)} matchs")
    return matches


if __name__ == "__main__":
    ms = load_matches()
    print(ms[:3])

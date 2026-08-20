"""Configuration centrale : chemins, clés, mapping des noms d'équipes."""
import os
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

# --- The Odds API (calendrier + cotes) ---
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "")
SPORT_KEY = "soccer_france_ligue_one"
ODDS_REGIONS = "eu"          # bookmakers européens
ODDS_MARKETS = "h2h"          # 1 / N / 2
ODDS_URL = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/odds"

# --- football-data.co.uk (historique, sans clé) ---
# 2526 = saison 2025-26 (précédente), 2627 = 2026-27 (en cours, grandit)
HISTORY_URLS = [
    ("https://www.football-data.co.uk/mmz4281/2627/F1.csv", 1.0),  # saison en cours
    ("https://www.football-data.co.uk/mmz4281/2526/F1.csv", 0.5),  # saison précédente
]

# Fenêtre de matchs à afficher (jours à venir)
UPCOMING_DAYS = 9
MAX_GOALS = 8          # troncature de la matrice de scores
DIXON_COLES_RHO = -0.05  # correction basse-fréquence (0-0,1-0,0-1,1-1)
HOME_WIN_BOOST = 1.05    # +5% sur la proba de victoire à domicile (l'avantage est déjà en partie dans les cotes)

# Les 18 clubs de Ligue 1 2026-2027. Nom canonique -> fragments reconnus dans
# les deux sources (Odds API, football-data.co.uk). Fragments assez spécifiques
# pour ne pas se chevaucher (ex. "paris fc" vs "paris saint").
TEAM_ALIASES = {
    "PSG":         ["paris saint", "paris sg", "psg"],
    "Paris FC":    ["paris fc"],
    "Marseille":   ["marseille"],
    "Lyon":        ["lyon", "lyonnais"],
    "Monaco":      ["monaco"],
    "Lille":       ["lille", "losc"],
    "Lens":        ["lens"],
    "Nice":        ["nice"],
    "Rennes":      ["rennes", "rennais"],
    "Strasbourg":  ["strasbourg"],
    "Brest":       ["brest", "brestois"],
    "Toulouse":    ["toulouse"],
    "Auxerre":     ["auxerre"],
    "Le Havre":    ["havre"],
    "Angers":      ["angers"],
    "Lorient":     ["lorient"],
    "Le Mans":     ["le mans", "mans fc"],   # promu 2026-27
    "Troyes":      ["troyes", "estac"],       # promu 2026-27
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def canon(name: str) -> str:
    """Ramène un nom d'équipe (quelle que soit la source) à son nom canonique."""
    n = _norm(name)
    # d'abord les alias multi-mots (plus spécifiques)
    for canonical, frags in sorted(TEAM_ALIASES.items(),
                                   key=lambda kv: -max(len(f) for f in kv[1])):
        for f in frags:
            if f in n:
                return canonical
    return name.strip()  # inconnue : garde le nom brut, traitée en moyenne ligue

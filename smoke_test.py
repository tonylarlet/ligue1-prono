"""Test local sans clé API : historique réel + faux marché."""
import json
from datetime import datetime, timezone, timedelta
from src.fetch_history import load_matches
from src.model import (fit_strengths, score_matrix, blend_with_market, best_score,
                       apply_home_boost)
from src import config

s = fit_strengths(load_matches())
print("mu =", round(s["mu"], 3), "| home_adv =", round(s["home_adv"], 3),
      "| équipes calibrées :", len(s["att"]))

# faux match avec un marché plausible
fake = [
    ("PSG", "Nantes", {"H": 0.80, "D": 0.13, "A": 0.07}),
    ("Marseille", "Lyon", {"H": 0.46, "D": 0.27, "A": 0.27}),
    ("Brest", "Monaco", {"H": 0.30, "D": 0.28, "A": 0.42}),
]
preds = []
for home, away, mk0 in fake:
    mk = apply_home_boost(mk0, config.HOME_WIN_BOOST)
    M = score_matrix(s, home, away)
    Q = blend_with_market(M, mk)
    (a, b), ep, top = best_score(Q, mk)
    winner = home if mk["H"] == max(mk.values()) else (away if mk["A"] == max(mk.values()) else "Nul")
    print(f"{home} {a}-{b} {away}  | EP={ep:.2f} | winner={winner} | alt={[t[0] for t in top]}")
    preds.append({"home": home, "away": away,
                  "commence": (datetime.now(timezone.utc)+timedelta(days=1)).isoformat(),
                  "proba": {"home": mk["H"], "draw": mk["D"], "away": mk["A"]},
                  "winner": winner, "winner_conf": max(mk.values()),
                  "score": f"{a}-{b}", "exp_points": round(ep, 3),
                  "alt_scores": [f"{i}-{j}" for (i, j), _p, _e in top]})

out = {"generated": datetime.now(timezone.utc).isoformat(), "count": len(preds),
       "predictions": preds}
config.DATA.mkdir(exist_ok=True)
(config.DATA / "predictions.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
from src.build_site import build
build()
print("OK")

"""Orchestrateur : historique + cotes -> data/predictions.json."""
import json
from datetime import datetime, timezone

from .config import DATA, HOME_WIN_BOOST
from .fetch_history import load_matches
from .fetch_odds import load_upcoming
from .model import (fit_strengths, score_matrix, blend_with_market, best_score,
                    apply_home_boost)

OUTCOME_FR = {"H": "domicile", "D": "nul", "A": "extérieur"}


def run():
    strengths = fit_strengths(load_matches())
    fixtures = load_upcoming()

    preds = []
    for fx in fixtures:
        mk = apply_home_boost(fx["market"], HOME_WIN_BOOST)
        M = score_matrix(strengths, fx["home"], fx["away"])
        Q = blend_with_market(M, mk)
        (a, b), ep, top = best_score(Q, mk)
        winner = max(mk, key=mk.get)
        if winner == "H":
            winner_team = fx["home"]
        elif winner == "A":
            winner_team = fx["away"]
        else:
            winner_team = "Match nul"
        preds.append({
            "home": fx["home"], "away": fx["away"],
            "commence": fx["commence"],
            "proba": {"home": round(mk["H"], 3), "draw": round(mk["D"], 3),
                       "away": round(mk["A"], 3)},
            "winner": winner_team,
            "winner_conf": round(mk[winner], 3),
            "score": f"{a}-{b}",
            "exp_points": round(ep, 3),
            "alt_scores": [f"{i}-{j}" for (i, j), _p, _e in top],
        })

    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "count": len(preds),
        "predictions": preds,
    }
    DATA.mkdir(exist_ok=True)
    (DATA / "predictions.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[predict] {len(preds)} pronostics écrits dans data/predictions.json")
    return out


if __name__ == "__main__":
    run()

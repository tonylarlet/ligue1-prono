"""Génère docs/index.html à partir de data/predictions.json."""
import json
from datetime import datetime, timezone, timedelta
from html import escape

from .config import DATA, DOCS


def _fr_datetime(iso):
    dt = datetime.fromisoformat(iso).astimezone(timezone(timedelta(hours=2)))
    jours = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
    return f"{jours[dt.weekday()]} {dt.day:02d}/{dt.month:02d} {dt.hour:02d}h{dt.minute:02d}"


def _bar(p):
    return f'<span class="bar" style="width:{p*100:.0f}%"></span>'


def build():
    data = json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))
    gen = _fr_datetime(data["generated"])
    cards = []
    for p in data["predictions"]:
        conf = p["winner_conf"]
        cls = "hi" if conf >= 0.55 else ("mid" if conf >= 0.40 else "lo")
        cards.append(f"""
    <article class="card {cls}">
      <div class="when">{escape(_fr_datetime(p['commence']))}</div>
      <div class="teams"><b>{escape(p['home'])}</b> <span>vs</span> <b>{escape(p['away'])}</b></div>
      <div class="score">{escape(p['score'])}</div>
      <div class="winner">Pronostic : <b>{escape(p['winner'])}</b> · confiance {conf*100:.0f}%</div>
      <div class="probs">
        <div>1 {p['proba']['home']*100:.0f}% {_bar(p['proba']['home'])}</div>
        <div>N {p['proba']['draw']*100:.0f}% {_bar(p['proba']['draw'])}</div>
        <div>2 {p['proba']['away']*100:.0f}% {_bar(p['proba']['away'])}</div>
      </div>
      <div class="alt">Autres scores probables : {escape(', '.join(p['alt_scores']))}</div>
    </article>""")

    html = f"""<!doctype html>
<html lang="fr"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pronostics Ligue 1</title>
<style>
  :root {{ --bg:#0f1420; --card:#1b2233; --line:#2a3347; --tx:#e8ecf4; --mut:#93a0b8;
          --hi:#22c55e; --mid:#eab308; --lo:#ef4444; --accent:#3b82f6; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--tx);
         font:15px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif; }}
  header {{ padding:24px 16px 8px; max-width:1000px; margin:0 auto; }}
  h1 {{ margin:0 0 4px; font-size:22px; }}
  .sub {{ color:var(--mut); font-size:13px; }}
  main {{ max-width:1000px; margin:0 auto; padding:16px;
         display:grid; gap:12px; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); }}
  .card {{ background:var(--card); border:1px solid var(--line); border-left:4px solid var(--mut);
          border-radius:12px; padding:14px 16px; }}
  .card.hi {{ border-left-color:var(--hi); }}
  .card.mid {{ border-left-color:var(--mid); }}
  .card.lo {{ border-left-color:var(--lo); }}
  .when {{ color:var(--mut); font-size:12px; text-transform:uppercase; letter-spacing:.04em; }}
  .teams {{ font-size:17px; margin:4px 0; }}
  .teams span {{ color:var(--mut); font-size:13px; margin:0 4px; }}
  .score {{ font-size:34px; font-weight:800; letter-spacing:2px; margin:6px 0 2px; color:var(--accent); }}
  .winner {{ font-size:13px; margin-bottom:10px; }}
  .probs > div {{ display:flex; align-items:center; gap:8px; font-size:12px;
                 color:var(--mut); margin:2px 0; }}
  .bar {{ display:inline-block; height:6px; background:var(--accent); border-radius:3px; }}
  .probs > div:nth-child(2) .bar {{ background:var(--mut); }}
  .alt {{ margin-top:10px; font-size:12px; color:var(--mut);
         border-top:1px solid var(--line); padding-top:8px; }}
  footer {{ max-width:1000px; margin:0 auto; padding:8px 16px 40px; color:var(--mut); font-size:12px; }}
</style></head><body>
<header>
  <h1>⚽ Pronostics Ligue 1</h1>
  <div class="sub">{data['count']} match(s) · mis à jour le {escape(gen)} (Paris) ·
    scores optimisés pour le barème Mon Petit Prono (3 pts score exact, 1 pt bon résultat) ·
    bonus +10% domicile</div>
</header>
<main>{''.join(cards) if cards else '<p>Aucun match à venir dans la fenêtre.</p>'}</main>
<footer>
  Modèle hybride : cotes bookmakers (issue 1/N/2) + Poisson attaque/défense (score exact).
  Prédictions probabilistes fournies à titre indicatif — aucun résultat garanti.
  Sources : The Odds API, football-data.co.uk.
</footer>
</body></html>"""
    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    print(f"[site] docs/index.html généré ({data['count']} matchs)")


if __name__ == "__main__":
    build()

# ⚽ Pronostics Ligue 1

Génère chaque semaine un pronostic (**vainqueur + score exact**) pour chaque match
de Ligue 1, optimisé pour le barème de **Mon Petit Prono** (3 pts score exact,
1 pt bon résultat), et publie une page web mise à jour automatiquement chaque mardi.

## Comment ça marche

1. **Cotes des bookmakers** (The Odds API) → probabilité de chaque issue 1 / N / 2.
   C'est le signal le plus fiable pour le **vainqueur**.
2. **Modèle Poisson attaque/défense** (calibré sur l'historique football-data.co.uk)
   → distribution des **scores exacts**.
3. **Fusion** : le vainqueur suit le marché, le score suit le modèle.
4. **Optimisation du pari** : pour chaque match on choisit le score qui maximise
   les points attendus `EP = 2·P(score exact) + P(bon résultat)`.

## Mise en route (une seule fois)

### 1. Clé API gratuite
- Crée un compte sur https://the-odds-api.com (gratuit, 500 requêtes/mois).
- Copie ta clé API.

### 2. Dépôt GitHub
```bash
cd ligue1-prono
git init && git add . && git commit -m "init"
git branch -M main
git remote add origin https://github.com/tonylarlet/ligue1-prono.git
git push -u origin main
```

### 3. Secret + Pages
- **Settings → Secrets and variables → Actions → New repository secret**
  - Nom : `ODDS_API_KEY` · Valeur : ta clé.
- **Settings → Pages** → Source : *Deploy from a branch* → Branch `main`, dossier `/docs`.
- Ta page : `https://tonylarlet.github.io/ligue1-prono/`

## Mise à jour

- **Automatique** : chaque mardi 06:00 UTC (~08:00 Paris).
- **À la demande** : onglet **Actions → Mise à jour pronostics → Run workflow**.

## En local (test)

```bash
pip install -r requirements.txt
export ODDS_API_KEY=xxxx        # PowerShell : $env:ODDS_API_KEY="xxxx"
python -m src.predict
python -m src.build_site
# ouvrir docs/index.html
```

## Limites

Prédictions probabilistes, **aucun résultat garanti**. L'objectif est de battre le
hasard sur la durée d'une saison, pas de gagner chaque match. En début de saison le
modèle s'appuie surtout sur les cotes (peu de données récentes).

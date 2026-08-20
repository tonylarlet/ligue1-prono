"""Modèle Poisson (forces attaque/défense) fusionné avec les cotes du marché."""
import math
from collections import defaultdict

from .config import MAX_GOALS, DIXON_COLES_RHO


def fit_strengths(matches):
    """Force d'attaque/défense de chaque équipe, relative à la moyenne ligue."""
    gf = defaultdict(float); ga = defaultdict(float); w = defaultdict(float)
    tot_goals = 0.0; tot_w = 0.0
    hg_sum = 0.0; ag_sum = 0.0
    for m in matches:
        wt = m["weight"]
        gf[m["home"]] += m["hg"] * wt; ga[m["home"]] += m["ag"] * wt
        gf[m["away"]] += m["ag"] * wt; ga[m["away"]] += m["hg"] * wt
        w[m["home"]] += wt; w[m["away"]] += wt
        tot_goals += (m["hg"] + m["ag"]) * wt
        tot_w += 2 * wt          # 2 équipes-matchs
        hg_sum += m["hg"] * wt; ag_sum += m["ag"] * wt
    if tot_w == 0:
        raise SystemExit("Aucune donnée historique pour calibrer le modèle.")
    mu = tot_goals / tot_w                    # buts moyens par équipe-match
    home_adv = math.sqrt((hg_sum + 1) / (ag_sum + 1))  # avantage du terrain
    att, dfn = {}, {}
    for t in w:
        att[t] = (gf[t] / w[t]) / mu if w[t] else 1.0
        dfn[t] = (ga[t] / w[t]) / mu if w[t] else 1.0
    return {"mu": mu, "home_adv": home_adv, "att": att, "dfn": dfn}


def apply_home_boost(market, boost):
    """Majore la proba de victoire domicile de `boost` (ex. 1.10 = +10%), renormalise."""
    h = market["H"] * boost
    d, a = market["D"], market["A"]
    s = h + d + a
    return {"H": h / s, "D": d / s, "A": a / s}


def _pois(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def _dc_tau(i, j, lh, la, rho):
    """Correction Dixon-Coles pour les petits scores."""
    if i == 0 and j == 0:
        return 1 - lh * la * rho
    if i == 0 and j == 1:
        return 1 + lh * rho
    if i == 1 and j == 0:
        return 1 + la * rho
    if i == 1 and j == 1:
        return 1 - rho
    return 1.0


def score_matrix(str_, home, away):
    """Matrice P[i][j] des scores (i buts domicile, j buts extérieur)."""
    att, dfn, mu, ha = str_["att"], str_["dfn"], str_["mu"], str_["home_adv"]
    ah = att.get(home, 1.0); dh = dfn.get(home, 1.0)
    aa = att.get(away, 1.0); da = dfn.get(away, 1.0)
    lh = mu * ah * da * ha
    la = mu * aa * dh / ha
    M = [[_pois(i, lh) * _pois(j, la) * _dc_tau(i, j, lh, la, DIXON_COLES_RHO)
          for j in range(MAX_GOALS + 1)] for i in range(MAX_GOALS + 1)]
    s = sum(sum(row) for row in M)
    return [[v / s for v in row] for row in M]


def _outcome_probs(M):
    pH = sum(M[i][j] for i in range(len(M)) for j in range(len(M)) if i > j)
    pD = sum(M[i][i] for i in range(len(M)))
    pA = sum(M[i][j] for i in range(len(M)) for j in range(len(M)) if i < j)
    return pH, pD, pA


def blend_with_market(M, market):
    """Recale la matrice pour que ses probas 1/N/2 égalent le marché.

    Le vainqueur suit le marché (signal le plus fiable) ; la forme des scores
    à l'intérieur de chaque issue reste celle du modèle Poisson.
    """
    pH, pD, pA = _outcome_probs(M)
    fH = market["H"] / pH if pH else 0
    fD = market["D"] / pD if pD else 0
    fA = market["A"] / pA if pA else 0
    Q = [[0.0] * len(M) for _ in M]
    for i in range(len(M)):
        for j in range(len(M)):
            f = fH if i > j else (fA if i < j else fD)
            Q[i][j] = M[i][j] * f
    return Q


def best_score(Q, market):
    """Score qui maximise les points attendus : EP = 2·P(exact) + P(bon résultat).

    Barème Mon Petit Prono : 3 pts score exact, 1 pt bon résultat, 0 sinon.
    """
    m = {"H": market["H"], "D": market["D"], "A": market["A"]}
    best, best_ep = (1, 1), -1.0
    ranked = []
    for i in range(min(7, len(Q))):
        for j in range(min(7, len(Q))):
            out = "H" if i > j else ("A" if i < j else "D")
            ep = 2 * Q[i][j] + m[out]
            ranked.append(((i, j), Q[i][j], ep))
            if ep > best_ep:
                best_ep, best = ep, (i, j)
    ranked.sort(key=lambda x: -x[1])       # scores les plus probables
    return best, best_ep, ranked[:4]

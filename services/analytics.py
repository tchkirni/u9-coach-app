import pandas as pd
from datetime import date, timedelta

from core.models import best_position_from_scores, compute_position_scores
from storage import repository as repo


def get_all_match_performances(data):
    """Retourne un DataFrame avec toutes les perfs de match, une ligne par joueur/match."""
    rows = []
    for match in data.get("matches", []):
        match_date = pd.to_datetime(match["date"]).date()
        for perf in match.get("performances", []):
            player = repo.find_player(data, perf["player_id"])
            if not player:
                continue
            overall = (perf["tech"] + perf["phys"] + perf["tact"] + perf["mental"]) / 4
            rows.append(
                {
                    "Joueur": player["name"],
                    "player_id": player["id"],
                    "date": match_date,
                    "overall": overall,
                    "Tech": perf["tech"],
                    "Phys": perf["phys"],
                    "Tact": perf["tact"],
                    "Mental": perf["mental"],
                    "Minutes": perf["minutes"],
                    "Buts": perf["goals"],
                    "Passes": perf["assists"],
                    "match_id": match["id"],
                    "adversaire": match["opponent"],
                    "competition": match["competition"],
                }
            )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def build_profile_rows(data):
    rows = []
    for player in data.get("players", []):
        scores = compute_position_scores(player)
        best_pos = best_position_from_scores(scores)
        row = {
            "Nom": player["name"],
            "Poste préf. (déclaré)": player.get("preferred_position") or "",
            "Poste recommandé (profil)": best_pos or "",
        }
        if scores:
            for pos in ["Gardien", "Défenseur", "Milieu", "Attaquant"]:
                row[f"Score {pos}"] = scores.get(pos)
        rows.append(row)
    return rows


def aggregate_match_means(data):
    all_perfs = []
    for match in data.get("matches", []):
        for perf in match.get("performances", []):
            player = repo.find_player(data, perf["player_id"])
            if not player:
                continue
            all_perfs.append(
                {
                    "Joueur": player["name"],
                    "Tech": perf["tech"],
                    "Phys": perf["phys"],
                    "Tact": perf["tact"],
                    "Mental": perf["mental"],
                    "Buts": perf["goals"],
                    "Passes": perf["assists"],
                }
            )

    if not all_perfs:
        return pd.DataFrame()

    dfp = pd.DataFrame(all_perfs)
    agg = dfp.groupby("Joueur").agg(
        {
            "Tech": "mean",
            "Phys": "mean",
            "Tact": "mean",
            "Mental": "mean",
            "Buts": "sum",
            "Passes": "sum",
        }
    ).round(2)
    return agg


def compute_progress_deltas(df_all, today=None):
    today = today or date.today()
    recent_start = today - timedelta(days=30)
    prev_start = today - timedelta(days=60)

    df_recent = df_all[df_all["date"] >= recent_start]
    df_prev = df_all[(df_all["date"] < recent_start) & (df_all["date"] >= prev_start)]

    if df_recent.empty or df_prev.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    recent_mean = df_recent.groupby("Joueur")["overall"].mean()
    prev_mean = df_prev.groupby("Joueur")["overall"].mean()

    df_delta = pd.DataFrame(
        {"Note 30 derniers jours": recent_mean, "Note 30–60 jours": prev_mean}
    ).dropna()

    if df_delta.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_delta["Delta"] = (
        df_delta["Note 30 derniers jours"] - df_delta["Note 30–60 jours"]
    ).round(2)
    top_up = df_delta.sort_values("Delta", ascending=False).head(5)
    top_down = df_delta.sort_values("Delta", ascending=True).head(5)
    return df_delta, top_up, top_down


def aggregate_minutes(df_all):
    agg_minutes = df_all.groupby("Joueur").agg(
        Matches=("overall", "count"),
        Minutes_totales=("Minutes", "sum"),
    )
    agg_minutes["Minutes / match"] = (
        agg_minutes["Minutes_totales"] / agg_minutes["Matches"]
    ).round(1)
    return agg_minutes


def top_three_for_match(df_all, match_id):
    df_match = df_all[df_all["match_id"] == match_id].copy()
    if df_match.empty:
        return pd.DataFrame()
    df_match["Note globale"] = df_match["overall"].round(2)
    return df_match.sort_values("Note globale", ascending=False).head(3)[
        ["Joueur", "Note globale", "Minutes", "Buts", "Passes"]
    ]

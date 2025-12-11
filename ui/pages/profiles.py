from datetime import date

import pandas as pd
import streamlit as st

from core.constants import SKILLS
from core.models import best_position_from_scores, compute_position_scores
from services.analytics import (
    aggregate_match_means,
    aggregate_minutes,
    build_profile_rows,
    compute_progress_deltas,
    get_all_match_performances,
    top_three_for_match,
)


def _render_base_ratings(repo, data):
    st.subheader("Notes de base & poste recommandé")

    if not data["players"]:
        st.warning("Ajoute d'abord des joueurs dans l’onglet 'Joueurs'.")
        return

    player_names = {p["name"]: p["id"] for p in data["players"]}
    selected_name = st.selectbox("Choisir un joueur", list(player_names.keys()))
    player = repo.find_player(data, player_names[selected_name])

    st.markdown(f"### {player['name']}")

    ratings = player.get("base_ratings", {})
    new_ratings = {}
    for skill in SKILLS:
        new_ratings[skill] = st.slider(
            skill,
            min_value=1, max_value=5,
            value=int(ratings.get(skill, 3)),
        )

    if st.button("💾 Enregistrer les notes"):
        player["base_ratings"] = new_ratings
        repo.save_data(data)
        st.success("Profil mis à jour.")

    if player.get("base_ratings"):
        scores = compute_position_scores(player)
        best_pos = best_position_from_scores(scores)
        st.subheader("Profils par poste (à partir des notes)")
        st.write(scores)
        if best_pos:
            st.success(f"Poste recommandé selon le profil : **{best_pos}**")


def _render_stats(repo, data):
    st.subheader("Profils, moyennes et tendances")

    if not data["players"]:
        st.warning("Aucun joueur.")
        return

    rows = build_profile_rows(data)
    df_profiles = pd.DataFrame(rows)
    st.markdown("#### Profils postes (profil de base)")
    st.dataframe(df_profiles, use_container_width=True)

    agg = aggregate_match_means(data)
    if agg.empty:
        st.info("Aucune performance de match saisie pour le moment.")
    else:
        st.markdown("#### Moyennes de match par joueur")
        st.dataframe(agg, use_container_width=True)

        st.markdown("#### Visualisation rapide – moyenne technique")
        st.bar_chart(agg["Tech"])

    st.markdown("---")
    st.markdown("#### Dashboard Coach")

    df_all = get_all_match_performances(data)
    if df_all.empty:
        st.info("Aucune performance de match saisie pour le moment.")
        return

    if not isinstance(df_all["date"].iloc[0], date):
        df_all["date"] = pd.to_datetime(df_all["date"]).dt.date

    st.markdown("##### Joueurs en progression / en difficulté (30j vs 30–60j)")
    _, top_up, top_down = compute_progress_deltas(df_all)

    if top_up.empty and top_down.empty:
        st.info("Pas assez de données pour comparer les 30 derniers jours aux 30 jours précédents.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("###### 📈 Joueurs en progression")
            st.dataframe(top_up, use_container_width=True)
        with col2:
            st.markdown("###### 📉 Joueurs en difficulté")
            st.dataframe(top_down, use_container_width=True)

    st.markdown("---")
    st.markdown("##### ⏱️ Temps de jeu & charge de travail")

    agg_minutes = aggregate_minutes(df_all)
    st.dataframe(
        agg_minutes.sort_values("Minutes_totales", ascending=False),
        use_container_width=True,
    )
    st.bar_chart(agg_minutes["Minutes_totales"])

    st.markdown("---")
    st.markdown("##### 🏅 Top 3 joueurs par match")

    match_labels = {
        f"{m['date']} – {m['opponent']} ({m['competition']})": m["id"]
        for m in data.get("matches", [])
    }

    if not match_labels:
        st.info("Aucun match enregistré.")
        return

    selected_match_label = st.selectbox("Choisir un match", list(match_labels.keys()))
    selected_match_id = match_labels[selected_match_label]

    top3 = top_three_for_match(df_all, selected_match_id)
    if top3.empty:
        st.info("Aucune performance enregistrée pour ce match.")
        return
    st.table(top3.set_index("Joueur"))


def render(repo, data):
    st.header("📊 Profils joueurs & analytics")

    tab_profiles, tab_stats = st.tabs(["Profils", "Stats / Dashboard"])
    with tab_profiles:
        _render_base_ratings(repo, data)
    with tab_stats:
        _render_stats(repo, data)

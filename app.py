import streamlit as st
import pandas as pd
from datetime import date

from core.constants import POSITION_WEIGHTS, SKILLS
from core.models import best_position_from_scores, compute_position_scores
from services.analytics import (
    aggregate_match_means,
    aggregate_minutes,
    build_profile_rows,
    compute_progress_deltas,
    get_all_match_performances,
    top_three_for_match,
)
from services.reports import generate_player_pdf
from storage import repository as repo

def apply_mobile_theme():
    """Ajuste le style pour une utilisation mobile (gros boutons, champs lisibles)."""
    st.markdown(
        """
        <style>
        /* Réduire un peu les marges globales sur mobile */
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.7rem !important;
                padding-right: 0.7rem !important;
                padding-top: 0.5rem !important;
            }
        }

        /* Gros boutons (boutons classiques + download button) */
        .stButton > button, .stDownloadButton > button {
            border-radius: 999px;
            padding: 0.8rem 1.6rem;
            font-size: 1.1rem;
            font-weight: 600;
            width: 100%;
        }

        /* Inputs plus lisibles */
        .stTextInput > div > input,
        .stNumberInput input {
            font-size: 1.05rem;
            padding-top: 0.45rem;
            padding-bottom: 0.45rem;
        }

        /* Selectbox plus hautes */
        .stSelectbox > div > div {
            font-size: 1.05rem;
            padding-top: 0.3rem;
            padding-bottom: 0.3rem;
        }

        /* Sliders un peu plus “touch friendly” */
        .stSlider > div[data-baseweb="slider"] {
            padding-top: 0.7rem;
            padding-bottom: 0.2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# UI – Joueurs
# =========================================================

def page_players(repo, data):
    st.header("👥 Gestion des joueurs")

    with st.form("add_player"):
        st.subheader("Ajouter un joueur")
        name = st.text_input("Nom du joueur")
        birth_year = st.number_input("Année de naissance", min_value=2010, max_value=2030, value=2016)
        preferred_position = st.selectbox(
            "Poste préférentiel",
            ["", "Gardien", "Défenseur", "Milieu", "Attaquant"]
        )
        foot = st.selectbox("Pied fort", ["", "Droit", "Gauche", "Ambidextre"])
        submit = st.form_submit_button("Ajouter le joueur")

    if submit and name.strip():
        new_player = {
            "id": repo.get_next_id(data["players"]),
            "name": name.strip(),
            "birth_year": int(birth_year),
            "preferred_position": preferred_position or None,
            "foot": foot or None,
            "base_ratings": {},
        }
        data["players"].append(new_player)
        repo.save_data(data)
        st.success(f"Joueur '{name}' ajouté.")

    if data["players"]:
        st.subheader("Liste des joueurs")
        df = pd.DataFrame([
            {
                "ID": p["id"],
                "Nom": p["name"],
                "Année": p.get("birth_year"),
                "Poste préf.": p.get("preferred_position") or "",
                "Pied": p.get("foot") or "",
            }
            for p in data["players"]
        ])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucun joueur pour l’instant.")


# =========================================================
# UI – Profil technique
# =========================================================

def page_base_ratings(repo, data):
    st.header("📊 Profil technique / physique / tactique / mental")

    if not data["players"]:
        st.warning("Ajoute d'abord des joueurs dans l’onglet 'Joueurs'.")
        return

    player_names = {p["name"]: p["id"] for p in data["players"]}
    selected_name = st.selectbox("Choisir un joueur", list(player_names.keys()))
    player = repo.find_player(data, player_names[selected_name])

    st.subheader(f"Notes de base – {player['name']}")

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


# =========================================================
# UI – Entraînements (NEW)
# =========================================================

def page_trainings(repo, data):
    st.header("🏋️ Entraînements")

    if not data["players"]:
        st.warning("Ajoute d'abord des joueurs dans l’onglet 'Joueurs'.")
        return

    # --- Créer une séance ---
    st.subheader("Créer une nouvelle séance")

    with st.form("create_training"):
        t_date = st.date_input("Date de l’entraînement", value=date.today())
        theme = st.text_input("Thème (ex : conduite de balle, jeu réduit…)")
        t_type = st.selectbox(
            "Type de séance",
            ["Technique", "Physique", "Match / Jeu", "Coordination / Motricité", "Autre"],
        )
        notes = st.text_area("Notes / Objectifs de la séance")
        submit_training = st.form_submit_button("Créer la séance")

    if submit_training and theme.strip():
        new_training = {
            "id": repo.get_next_id(data["trainings"]),
            "date": t_date.isoformat(),
            "theme": theme.strip(),
            "type": t_type,
            "notes": notes.strip(),
            "attendances": [],  # une entrée par joueur
        }
        data["trainings"].append(new_training)
        repo.save_data(data)
        st.success(f"Séance du {t_date} créée.")

    if not data["trainings"]:
        st.info("Aucune séance enregistrée pour l’instant.")
        return

    # --- Sélection d’une séance ---
    st.subheader("Feuille de présence & implication")

    training_options = {
        f"{t['date']} – {t['theme']} ({t['type']})": t["id"]
        for t in sorted(data["trainings"], key=lambda x: x["date"], reverse=True)
    }
    selected_label = st.selectbox("Choisir une séance", list(training_options.keys()))
    training = repo.find_training(data, training_options[selected_label])

    st.markdown(f"**Date :** {training['date']}  \n**Thème :** {training['theme']}  \n**Type :** {training['type']}")
    if training.get("notes"):
        st.markdown(f"**Objectifs / Notes :** {training['notes']}")

    # Indexer les présences existantes par player_id
    existing = {a["player_id"]: a for a in training.get("attendances", [])}

    st.markdown("---")
    st.subheader("Présence & comportement par joueur")

    with st.form("update_attendance"):
        rows = []
        for p in data["players"]:
            att = existing.get(p["id"], {})
            st.markdown(f"### {p['name']}")
            col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
            with col1:
                present = st.checkbox("Présent", value=att.get("present", True), key=f"present_{p['id']}")
            with col2:
                effort = st.slider(
                    "Effort (1-5)",
                    1, 5,
                    value=int(att.get("effort", 3)),
                    key=f"effort_{p['id']}",
                )
            with col3:
                focus = st.slider(
                    "Concentration (1-5)",
                    1, 5,
                    value=int(att.get("focus", 3)),
                    key=f"focus_{p['id']}",
                )
            with col4:
                comment = st.text_input(
                    "Commentaire",
                    value=att.get("comment", ""),
                    key=f"comment_{p['id']}",
                )

            rows.append(
                (p["id"], present, effort, focus, comment)
            )

        submit_att = st.form_submit_button("💾 Enregistrer la séance")

    if submit_att:
        new_attendances = []
        for player_id, present, effort, focus, comment in rows:
            new_attendances.append(
                {
                    "player_id": player_id,
                    "present": bool(present),
                    "effort": int(effort),
                    "focus": int(focus),
                    "comment": comment.strip(),
                }
            )
        training["attendances"] = new_attendances
        repo.save_data(data)
        st.success("Séance mise à jour.")

    # Tableau récap
    if training.get("attendances"):
        st.subheader("Récapitulatif séance")

        table_rows = []
        for att in training["attendances"]:
            p = repo.find_player(data, att["player_id"])
            table_rows.append(
                {
                    "Joueur": p["name"] if p else "Inconnu",
                    "Présent": "Oui" if att["present"] else "Non",
                    "Effort": att["effort"],
                    "Concentration": att["focus"],
                    "Commentaire": att["comment"],
                }
            )
        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True)


# =========================================================
# UI – Matchs
# =========================================================

def page_matches(repo, data):
    st.header("🏟️ Matchs & performances")
    mobile_mode = st.session_state.get("mobile_mode", False)

    if mobile_mode:
        # Saisie plus simple, tout en colonne
        st.subheader("Saisie rapide (mobile)")
        # ici tu peux garder tes inputs les uns sous les autres
        col1 = col2 = None  # pour être explicite, mais tu peux juste faire tout en vertical
    else:
        col1, col2 = st.columns(2)

    # --- Création d’un match ---
    st.subheader("Créer un nouveau match")
    with st.form("create_match"):
        m_date = st.date_input("Date", value=date.today())
        opponent = st.text_input("Adversaire")
        competition = st.text_input("Compétition / Lieu")
        submit_match = st.form_submit_button("Créer le match")

    if submit_match and opponent.strip():
        new_match = {
            "id": repo.get_next_id(data["matches"]),
            "date": m_date.isoformat(),
            "opponent": opponent.strip(),
            "competition": competition.strip(),
            "performances": [],
        }
        data["matches"].append(new_match)
        repo.save_data(data)
        st.success(f"Match vs {opponent} ajouté.")

    if not data["matches"]:
        st.info("Aucun match enregistré pour l’instant.")
        return

    # Liste des matchs
    st.subheader("Ajouter des performances à un match")
    match_options = {
        f"{m['date']} – {m['opponent']} ({m['competition']})": m["id"]
        for m in sorted(data["matches"], key=lambda x: x["date"], reverse=True)
    }
    selected_match_label = st.selectbox("Choisir un match", list(match_options.keys()))
    match = repo.find_match(data, match_options[selected_match_label])

    if not data["players"]:
        st.warning("Ajoute des joueurs avant de saisir des performances.")
        return

    st.markdown("---")
    st.subheader("Ajouter une performance joueur pour ce match")

    player_names = {p["name"]: p["id"] for p in data["players"]}
    perf_player_name = st.selectbox("Joueur", list(player_names.keys()))
    perf_player = repo.find_player(data, player_names[perf_player_name])

    col1, col2 = st.columns(2)
    with col1:
        position_played = st.selectbox("Poste joué", ["Gardien", "Défenseur", "Milieu", "Attaquant"])
        minutes = st.number_input("Minutes jouées", min_value=0, max_value=90, value=40, step=5)
        goals = st.number_input("Buts", min_value=0, max_value=10, value=0)
        assists = st.number_input("Passes décisives", min_value=0, max_value=10, value=0)
    with col2:
        tech = st.slider("Note Technique (1-5)", 1, 5, 3)
        phys = st.slider("Note Physique (1-5)", 1, 5, 3)
        tact = st.slider("Note Tactique (1-5)", 1, 5, 3)
        mental = st.slider("Note Mentale (1-5)", 1, 5, 3)

    comment = st.text_area("Commentaires")

    if st.button("➕ Ajouter cette performance"):
        perf = {
            "player_id": perf_player["id"],
            "position": position_played,
            "minutes": int(minutes),
            "tech": int(tech),
            "phys": int(phys),
            "tact": int(tact),
            "mental": int(mental),
            "goals": int(goals),
            "assists": int(assists),
            "comment": comment.strip(),
        }
        match["performances"].append(perf)
        repo.save_data(data)
        st.success(f"Performance ajoutée pour {perf_player['name']}.")

    if match["performances"]:
        st.subheader("Performances déjà saisies pour ce match")
        rows = []
        for perf in match["performances"]:
            p = repo.find_player(data, perf["player_id"])
            rows.append({
                "Joueur": p["name"] if p else "Inconnu",
                "Poste": perf["position"],
                "Minutes": perf["minutes"],
                "Tech": perf["tech"],
                "Phys": perf["phys"],
                "Tact": perf["tact"],
                "Mental": perf["mental"],
                "Buts": perf["goals"],
                "Passes": perf["assists"],
                "Commentaire": perf["comment"],
            })
        df_match = pd.DataFrame(rows)
        st.dataframe(df_match, use_container_width=True)


# =========================================================
# UI – Stats & Profils
# =========================================================

def page_stats(repo, data):
    st.header("📈 Stats & profils")

    if not data["players"]:
        st.warning("Aucun joueur.")
        return

    rows = build_profile_rows(data)
    df_profiles = pd.DataFrame(rows)
    st.subheader("Profils postes (profil de base)")
    st.dataframe(df_profiles, use_container_width=True)

    agg = aggregate_match_means(data)
    if agg.empty:
        st.info("Aucune performance de match saisie pour le moment.")
    else:
        st.subheader("Moyennes de match par joueur")
        st.dataframe(agg, use_container_width=True)

        st.subheader("Visualisation rapide – moyenne technique")
        st.bar_chart(agg["Tech"])

    # --------- Fiche joueur PDF ---------
    st.markdown("---")
    st.subheader("📄 Fiche joueur (PDF)")

    player_names = {p["name"]: p["id"] for p in data["players"]}
    selected_name = st.selectbox("Choisir un joueur pour générer sa fiche PDF", list(player_names.keys()))

    if st.button("Générer la fiche PDF"):
        player = repo.find_player(data, player_names[selected_name])
        pdf_bytes = generate_player_pdf(player, data)
        file_name = f"Fiche_{player['name'].replace(' ', '_')}.pdf"

        st.download_button(
            label="📥 Télécharger la fiche joueur (PDF)",
            data=pdf_bytes,
            file_name=file_name,
            mime="application/pdf"
        )

def page_coach_dashboard(repo, data):
    st.header("📊 Dashboard Coach")

    df_all = get_all_match_performances(data)
    if df_all.empty:
        st.info("Aucune performance de match saisie pour le moment.")
        return

    # Assure que la colonne date est bien de type date
    if not isinstance(df_all["date"].iloc[0], date):
        df_all["date"] = pd.to_datetime(df_all["date"]).dt.date

    st.subheader("Joueurs en progression / en difficulté (30j vs 30–60j)")

    df_delta, top_up, top_down = compute_progress_deltas(df_all)

    if top_up.empty and top_down.empty:
        st.info("Pas assez de données pour comparer les 30 derniers jours aux 30 jours précédents.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📈 Joueurs en progression")
            st.dataframe(top_up, use_container_width=True)
        with col2:
            st.markdown("### 📉 Joueurs en difficulté")
            st.dataframe(top_down, use_container_width=True)

    st.markdown("---")

    # -------- Temps de jeu total / charge physique --------
    st.subheader("⏱️ Temps de jeu & charge de travail")

    agg_minutes = aggregate_minutes(df_all)
    st.dataframe(agg_minutes.sort_values("Minutes_totales", ascending=False),
                 use_container_width=True)

    st.markdown("##### Charge de travail physique (minutes accumulées)")
    st.bar_chart(agg_minutes["Minutes_totales"])

    st.markdown("---")

    # -------- Top 3 joueurs par match --------
    st.subheader("🏅 Top 3 joueurs par match")

    match_labels = {}
    for m in data.get("matches", []):
        label = f"{m['date']} – {m['opponent']} ({m['competition']})"
        match_labels[label] = m["id"]

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

# =========================================================
# Main
# =========================================================

def main():
    st.set_page_config(page_title="Suivi U9", layout="wide")

    apply_mobile_theme()

    st.title("⚽ Suivi U9 – Joueurs, Entraînements, Matchs & Profils postes")

    data = repo.load_data()

   
    mobile_mode = st.sidebar.checkbox("Mode mobile (terrain)", value=True)
    st.session_state["mobile_mode"] = mobile_mode

    page = st.sidebar.radio(
        "Navigation",
        ["Joueurs", "Profil technique", "Entraînements",
         "Matchs", "Stats & Profils", "Dashboard Coach"],
    )


    if page == "Joueurs":
        page_players(repo, data)
    elif page == "Profil technique":
        page_base_ratings(repo, data)
    elif page == "Entraînements":
        page_trainings(repo, data)
    elif page == "Matchs":
        page_matches(repo, data)
    elif page == "Stats & Profils":
        page_stats(repo, data)
    elif page == "Dashboard Coach":
        page_coach_dashboard(repo, data)


if __name__ == "__main__":
    main()


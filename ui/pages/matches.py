from datetime import date

import pandas as pd
import streamlit as st


def render(repo, data):
    st.header("🏟️ Matchs & performances")
    mobile_mode = st.session_state.get("mobile_mode", False)

    if mobile_mode:
        st.subheader("Saisie rapide (mobile)")
    else:
        st.subheader("Saisie standard")

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

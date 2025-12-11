from datetime import date

import pandas as pd
import streamlit as st


def render(repo, data):
    st.header("🏋️ Entraînements")

    if not data["players"]:
        st.warning("Ajoute d'abord des joueurs dans l’onglet 'Joueurs'.")
        return

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
            "attendances": [],
        }
        data["trainings"].append(new_training)
        repo.save_data(data)
        st.success(f"Séance du {t_date} créée.")

    if not data["trainings"]:
        st.info("Aucune séance enregistrée pour l’instant.")
        return

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

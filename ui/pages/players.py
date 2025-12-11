import pandas as pd
import streamlit as st


def render(repo, data):
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

import json

import streamlit as st

from services.reports import generate_player_pdf


def render(repo, data):
    st.header("📤 Exports & rapports")

    st.subheader("Exporter les données brutes")
    json_data = json.dumps(data, ensure_ascii=False, indent=2)
    st.download_button(
        label="📥 Télécharger les données (JSON)",
        data=json_data,
        file_name="u9_data.json",
        mime="application/json",
    )

    st.markdown("---")
    st.subheader("📄 Fiche joueur (PDF)")

    if not data["players"]:
        st.info("Ajoute d'abord des joueurs pour générer une fiche.")
        return

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

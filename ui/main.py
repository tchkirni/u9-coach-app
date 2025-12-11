import streamlit as st

from storage import repository as repo
from ui.pages import exports, matches, players, profiles, trainings
from ui.theme import apply_mobile_theme


PAGES = {
    "Joueurs": players.render,
    "Profils": profiles.render,
    "Entraînements": trainings.render,
    "Matchs": matches.render,
    "Exports": exports.render,
}


def main():
    st.set_page_config(page_title="Suivi U9", layout="wide")

    apply_mobile_theme()

    st.title("⚽ Suivi U9 – Joueurs, Entraînements, Matchs & Profils postes")

    data = repo.load_data()

    mobile_mode = st.sidebar.checkbox("Mode mobile (terrain)", value=True)
    st.session_state["mobile_mode"] = mobile_mode

    page = st.sidebar.selectbox("Navigation", list(PAGES.keys()))

    render_page = PAGES[page]
    render_page(repo, data)


if __name__ == "__main__":
    main()

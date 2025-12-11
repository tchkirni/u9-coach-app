import streamlit as st


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
            line-height: 1.4 !important;  /* évite que le texte soit "coupé" visuellement */
        }

        /* Selectbox plus hautes */
        .stSelectbox > div > div {
            font-size: 1.05rem;
            padding-top: 0.3rem;
            padding-bottom: 0.3rem;
            line-height: 1.4 !important;  /* évite que le texte soit "coupé" visuellement */
        }
        /* Garde le texte centré et non coupé dans la valeur sélectionnée */
        .stSelectbox [data-baseweb="select"] > div {
            min-height: 2.9rem;
            padding-top: 0.35rem;
            padding-bottom: 0.35rem;
            align-items: center;
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

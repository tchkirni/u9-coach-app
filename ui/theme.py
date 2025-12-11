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

        /* Inputs plus lisibles (évite le texte coupé visuellement) */
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        div[data-baseweb="input"] input {
            font-size: 1.05rem;
            padding-top: 0.7rem;
            padding-bottom: 0.7rem;
            line-height: 1.5 !important;
            min-height: 2.9rem;
        }

        /* Selectbox et multiselect : augmente la hauteur et la line-height du contenu */
        .stSelectbox div[data-baseweb="select"],
        .stMultiSelect div[data-baseweb="select"] {
            min-height: 2.9rem;
            font-size: 1.05rem;
        }

        .stSelectbox div[data-baseweb="select"] div[role="button"],
        .stMultiSelect div[data-baseweb="select"] div[role="button"] {
            padding-top: 0.55rem;
            padding-bottom: 0.55rem;
            line-height: 1.6 !important;
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

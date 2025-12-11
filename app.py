import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import date, datetime, timedelta

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from core.constants import POSITION_WEIGHTS, SKILLS
from core.models import best_position_from_scores, compute_position_scores

DATA_FILE = Path("u9_data.json")

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
# Fonctions de persistance
# =========================================================

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    # Sécurisation des structures (pour compatibilité avec anciennes versions)
    if "players" not in data:
        data["players"] = []
    if "matches" not in data:
        data["matches"] = []
    if "trainings" not in data:  # NEW
        data["trainings"] = []

    return data


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_next_id(items):
    if not items:
        return 1
    return max(item["id"] for item in items) + 1


def find_player(data, player_id):
    for p in data["players"]:
        if p["id"] == player_id:
            return p
    return None


def find_match(data, match_id):
    for m in data["matches"]:
        if m["id"] == match_id:
            return m
    return None


def find_training(data, training_id):  # NEW
    for t in data["trainings"]:
        if t["id"] == training_id:
            return t
    return None


def generate_player_pdf(player, data):
    """
    Génère un PDF (en mémoire) avec la fiche complète du joueur.
    Retourne un bytes (ready pour st.download_button).
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Marges & position de départ
    x_margin = 40
    y = height - 50

    def line(text, size=10, bold=False, dy=14):
        nonlocal y
        if y < 60:  # nouvelle page si trop bas
            c.showPage()
            y = height - 50
        if bold:
            c.setFont("Helvetica-Bold", size)
        else:
            c.setFont("Helvetica", size)
        c.drawString(x_margin, y, text)
        y -= dy

    # ========= En-tête =========
    line("FICHE JOUEUR – U9", size=16, bold=True, dy=22)
    line(f"Nom : {player.get('name', '')}", size=12, bold=True)
    line(f"Année de naissance : {player.get('birth_year', '')}", size=10)
    line(f"Poste préférentiel (déclaré) : {player.get('preferred_position', '')}", size=10)
    line(f"Pied fort : {player.get('foot', '')}", size=10)
    line(" ", dy=10)

    # ========= Profil de base =========
    base = player.get("base_ratings", {})
    line("Profil technique / physique / tactique / mental", size=12, bold=True, dy=18)
    if not base:
        line("Aucune note de base saisie pour l’instant.", size=10)
    else:
        for skill in SKILLS:
            val = base.get(skill)
            if val is not None:
                line(f"{skill} : {val}/5", size=10)

    line(" ", dy=10)

    # ========= Profils par poste =========
    scores = compute_position_scores(player)
    best_pos = best_position_from_scores(scores)
    line("Profil par poste (pondéré)", size=12, bold=True, dy=18)
    if scores:
        for pos in ["Gardien", "Défenseur", "Milieu", "Attaquant"]:
            sc = scores.get(pos)
            if sc is not None:
                line(f"{pos} : {sc}/5", size=10)
    if best_pos:
        line(f"➡ Poste recommandé : {best_pos}", size=11, bold=True, dy=16)

    line(" ", dy=10)

    # ========= Stats Entraînements =========
    # Présence, effort, concentration
    attendances = []
    for t in data.get("trainings", []):
        for att in t.get("attendances", []):
            if att.get("player_id") == player["id"]:
                attendances.append(att)

    line("Entraînements", size=12, bold=True, dy=18)
    if attendances:
        total_sessions = len(attendances)
        present_sessions = sum(1 for a in attendances if a.get("present"))
        avg_effort = round(sum(a.get("effort", 0) for a in attendances) / total_sessions, 2)
        avg_focus = round(sum(a.get("focus", 0) for a in attendances) / total_sessions, 2)
        line(f"Séances suivies : {present_sessions} / {total_sessions}", size=10)
        line(f"Effort moyen : {avg_effort}/5", size=10)
        line(f"Concentration moyenne : {avg_focus}/5", size=10)
    else:
        line("Aucune séance renseignée pour ce joueur.", size=10)

    line(" ", dy=10)

    # ========= Stats Matchs =========
    perfs = []
    for m in data.get("matches", []):
        for perf in m.get("performances", []):
            if perf.get("player_id") == player["id"]:
                perfs.append(perf)

    line("Matchs", size=12, bold=True, dy=18)
    if perfs:
        dfp = pd.DataFrame(perfs)
        avg_tech = round(dfp["tech"].mean(), 2)
        avg_phys = round(dfp["phys"].mean(), 2)
        avg_tact = round(dfp["tact"].mean(), 2)
        avg_mental = round(dfp["mental"].mean(), 2)
        total_goals = int(dfp["goals"].sum())
        total_assists = int(dfp["assists"].sum())

        line(f"Nombre de feuilles de match : {len(perfs)}", size=10)
        line(f"Tech / Phys / Tact / Mental (moyennes) : {avg_tech} / {avg_phys} / {avg_tact} / {avg_mental}", size=10)
        line(f"Buts : {total_goals}  |  Passes décisives : {total_assists}", size=10)
    else:
        line("Aucune performance de match saisie pour ce joueur.", size=10)

    line(" ", dy=10)

    # ========= Espace pour coach =========
    line("Zone coach – Points forts :", size=11, bold=True, dy=18)
    line("________________________________________", size=10)
    line("________________________________________", size=10)
    line("________________________________________", size=10)
    line(" ", dy=8)
    line("Zone coach – Axes de progression :", size=11, bold=True, dy=18)
    line("________________________________________", size=10)
    line("________________________________________", size=10)
    line("________________________________________", size=10)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# =========================================================
# UI – Joueurs
# =========================================================

def page_players(data):
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
            "id": get_next_id(data["players"]),
            "name": name.strip(),
            "birth_year": int(birth_year),
            "preferred_position": preferred_position or None,
            "foot": foot or None,
            "base_ratings": {},
        }
        data["players"].append(new_player)
        save_data(data)
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

def page_base_ratings(data):
    st.header("📊 Profil technique / physique / tactique / mental")

    if not data["players"]:
        st.warning("Ajoute d'abord des joueurs dans l’onglet 'Joueurs'.")
        return

    player_names = {p["name"]: p["id"] for p in data["players"]}
    selected_name = st.selectbox("Choisir un joueur", list(player_names.keys()))
    player = find_player(data, player_names[selected_name])

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
        save_data(data)
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

def page_trainings(data):
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
            "id": get_next_id(data["trainings"]),
            "date": t_date.isoformat(),
            "theme": theme.strip(),
            "type": t_type,
            "notes": notes.strip(),
            "attendances": [],  # une entrée par joueur
        }
        data["trainings"].append(new_training)
        save_data(data)
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
    training = find_training(data, training_options[selected_label])

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
        save_data(data)
        st.success("Séance mise à jour.")

    # Tableau récap
    if training.get("attendances"):
        st.subheader("Récapitulatif séance")

        table_rows = []
        for att in training["attendances"]:
            p = find_player(data, att["player_id"])
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

def page_matches(data):
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
            "id": get_next_id(data["matches"]),
            "date": m_date.isoformat(),
            "opponent": opponent.strip(),
            "competition": competition.strip(),
            "performances": [],
        }
        data["matches"].append(new_match)
        save_data(data)
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
    match = find_match(data, match_options[selected_match_label])

    if not data["players"]:
        st.warning("Ajoute des joueurs avant de saisir des performances.")
        return

    st.markdown("---")
    st.subheader("Ajouter une performance joueur pour ce match")

    player_names = {p["name"]: p["id"] for p in data["players"]}
    perf_player_name = st.selectbox("Joueur", list(player_names.keys()))
    perf_player = find_player(data, player_names[perf_player_name])

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
        save_data(data)
        st.success(f"Performance ajoutée pour {perf_player['name']}.")

    if match["performances"]:
        st.subheader("Performances déjà saisies pour ce match")
        rows = []
        for perf in match["performances"]:
            p = find_player(data, perf["player_id"])
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

def get_all_match_performances(data):
    """Retourne un DataFrame avec toutes les perfs de match, une ligne par joueur/match."""
    rows = []
    for m in data.get("matches", []):
        match_date = datetime.fromisoformat(m["date"]).date()
        for perf in m.get("performances", []):
            p = find_player(data, perf["player_id"])
            if not p:
                continue
            overall = (perf["tech"] + perf["phys"] + perf["tact"] + perf["mental"]) / 4
            rows.append({
                "Joueur": p["name"],
                "player_id": p["id"],
                "date": match_date,
                "overall": overall,
                "Tech": perf["tech"],
                "Phys": perf["phys"],
                "Tact": perf["tact"],
                "Mental": perf["mental"],
                "Minutes": perf["minutes"],
                "Buts": perf["goals"],
                "Passes": perf["assists"],
                "match_id": m["id"],
                "adversaire": m["opponent"],
                "competition": m["competition"],
            })
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def page_stats(data):
    st.header("📈 Stats & profils")

    if not data["players"]:
        st.warning("Aucun joueur.")
        return

    # Profils par poste (notes de base)
    rows = []
    for p in data["players"]:
        scores = compute_position_scores(p)
        best_pos = best_position_from_scores(scores)
        row = {
            "Nom": p["name"],
            "Poste préf. (déclaré)": p.get("preferred_position") or "",
            "Poste recommandé (profil)": best_pos or "",
        }
        if scores:
            for pos in ["Gardien", "Défenseur", "Milieu", "Attaquant"]:
                row[f"Score {pos}"] = scores.get(pos)
        rows.append(row)

    df_profiles = pd.DataFrame(rows)
    st.subheader("Profils postes (profil de base)")
    st.dataframe(df_profiles, use_container_width=True)

    # Stats de match
    all_perfs = []
    for m in data["matches"]:
        for perf in m["performances"]:
            p = find_player(data, perf["player_id"])
            if not p:
                continue
            all_perfs.append({
                "Joueur": p["name"],
                "Tech": perf["tech"],
                "Phys": perf["phys"],
                "Tact": perf["tact"],
                "Mental": perf["mental"],
                "Buts": perf["goals"],
                "Passes": perf["assists"],
            })

    if all_perfs:
        dfp = pd.DataFrame(all_perfs)
        st.subheader("Moyennes de match par joueur")
        agg = dfp.groupby("Joueur").agg({
            "Tech": "mean",
            "Phys": "mean",
            "Tact": "mean",
            "Mental": "mean",
            "Buts": "sum",
            "Passes": "sum",
        }).round(2)
        st.dataframe(agg, use_container_width=True)

        st.subheader("Visualisation rapide – moyenne technique")
        st.bar_chart(agg["Tech"])
    else:
        st.info("Aucune performance de match saisie pour le moment.")

    # --------- Fiche joueur PDF ---------
    st.markdown("---")
    st.subheader("📄 Fiche joueur (PDF)")

    player_names = {p["name"]: p["id"] for p in data["players"]}
    selected_name = st.selectbox("Choisir un joueur pour générer sa fiche PDF", list(player_names.keys()))

    if st.button("Générer la fiche PDF"):
        player = find_player(data, player_names[selected_name])
        pdf_bytes = generate_player_pdf(player, data)
        file_name = f"Fiche_{player['name'].replace(' ', '_')}.pdf"

        st.download_button(
            label="📥 Télécharger la fiche joueur (PDF)",
            data=pdf_bytes,
            file_name=file_name,
            mime="application/pdf"
        )

def page_coach_dashboard(data):
    st.header("📊 Dashboard Coach")

    df_all = get_all_match_performances(data)
    if df_all.empty:
        st.info("Aucune performance de match saisie pour le moment.")
        return

    # Assure que la colonne date est bien de type date
    if not isinstance(df_all["date"].iloc[0], date):
        df_all["date"] = pd.to_datetime(df_all["date"]).dt.date

    today = date.today()
    recent_start = today - timedelta(days=30)
    prev_start = today - timedelta(days=60)

    # -------- Joueurs en progression / difficulté (delta notes vs dernier mois) --------
    st.subheader("Joueurs en progression / en difficulté (30j vs 30–60j)")

    df_recent = df_all[df_all["date"] >= recent_start]
    df_prev = df_all[(df_all["date"] < recent_start) & (df_all["date"] >= prev_start)]

    if df_recent.empty or df_prev.empty:
        st.info("Pas assez de données pour comparer les 30 derniers jours aux 30 jours précédents.")
    else:
        recent_mean = df_recent.groupby("Joueur")["overall"].mean()
        prev_mean = df_prev.groupby("Joueur")["overall"].mean()

        df_delta = pd.DataFrame({
            "Note 30 derniers jours": recent_mean,
            "Note 30–60 jours": prev_mean,
        }).dropna()

        if not df_delta.empty:
            df_delta["Delta"] = (df_delta["Note 30 derniers jours"]
                                 - df_delta["Note 30–60 jours"]).round(2)

            # Joueurs en progression (delta positif, triés décroissant)
            top_up = df_delta.sort_values("Delta", ascending=False).head(5)
            # Joueurs en difficulté (delta négatif, triés croissant)
            top_down = df_delta.sort_values("Delta", ascending=True).head(5)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📈 Joueurs en progression")
                st.dataframe(top_up, use_container_width=True)
            with col2:
                st.markdown("### 📉 Joueurs en difficulté")
                st.dataframe(top_down, use_container_width=True)
        else:
            st.info("Pas assez de joueurs ayant des matchs dans les deux périodes.")

    st.markdown("---")

    # -------- Temps de jeu total / charge physique --------
    st.subheader("⏱️ Temps de jeu & charge de travail")

    agg_minutes = df_all.groupby("Joueur").agg(
        Matches=("overall", "count"),
        Minutes_totales=("Minutes", "sum"),
    )
    agg_minutes["Minutes / match"] = (agg_minutes["Minutes_totales"]
                                      / agg_minutes["Matches"]).round(1)

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

    df_match = df_all[df_all["match_id"] == selected_match_id].copy()
    if df_match.empty:
        st.info("Aucune performance enregistrée pour ce match.")
        return

    df_match["Note globale"] = df_match["overall"].round(2)
    top3 = df_match.sort_values("Note globale", ascending=False).head(3)[
        ["Joueur", "Note globale", "Minutes", "Buts", "Passes"]
    ]
    st.table(top3.set_index("Joueur"))

# =========================================================
# Main
# =========================================================

def main():
    st.set_page_config(page_title="Suivi U9", layout="wide")

    apply_mobile_theme()

    st.title("⚽ Suivi U9 – Joueurs, Entraînements, Matchs & Profils postes")

    data = load_data()

   
    mobile_mode = st.sidebar.checkbox("Mode mobile (terrain)", value=True)
    st.session_state["mobile_mode"] = mobile_mode

    page = st.sidebar.radio(
        "Navigation",
        ["Joueurs", "Profil technique", "Entraînements",
         "Matchs", "Stats & Profils", "Dashboard Coach"],
    )


    if page == "Joueurs":
        page_players(data)
    elif page == "Profil technique":
        page_base_ratings(data)
    elif page == "Entraînements":
        page_trainings(data)
    elif page == "Matchs":
        page_matches(data)
    elif page == "Stats & Profils":
        page_stats(data)
    elif page == "Dashboard Coach":
        page_coach_dashboard(data)


if __name__ == "__main__":
    main()


from io import BytesIO

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from core.constants import SKILLS
from core.models import best_position_from_scores, compute_position_scores


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
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
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
    attendances = []
    for training in data.get("trainings", []):
        for att in training.get("attendances", []):
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
    for match in data.get("matches", []):
        for perf in match.get("performances", []):
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
        line(
            "Tech / Phys / Tact / Mental (moyennes) : "
            f"{avg_tech} / {avg_phys} / {avg_tact} / {avg_mental}",
            size=10,
        )
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

"""Admin: vede i risultati e puo' eliminarli."""
from flask import Blueprint, abort, flash, redirect, render_template, session, url_for

from db import get_scores, open_db

admin = Blueprint("admin", __name__, url_prefix="/admin")


def check_admin():
    if not session.get("username"):
        return redirect(url_for("frontend.login"))
    if session.get("role") != "admin":
        abort(403)
    return None


@admin.get("/")
def index():
    redirect_response = check_admin()
    if redirect_response:
        return redirect_response
    return render_template("admin.html", scores=get_scores())


@admin.post("/elimina/<int:score_id>")
def elimina(score_id):
    redirect_response = check_admin()
    if redirect_response:
        return redirect_response
    with open_db() as db:
        db.execute("DELETE FROM scores WHERE id = ?", (score_id,))
    flash("Risultato eliminato.")
    return redirect(url_for("admin.index"))

"""Pagine HTML: classifica, login e inserimento manuale."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from db import add_score, get_scores, open_db

frontend = Blueprint("frontend", __name__)


@frontend.get("/")
def index():
    return render_template("index.html", scores=get_scores())


@frontend.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with open_db() as db:
            user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("Accesso effettuato.")
            return redirect(url_for("frontend.index"))
        flash("Username o password errati.")
    return render_template("login.html")


@frontend.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("frontend.index"))


@frontend.route("/aggiungi", methods=["GET", "POST"])
def aggiungi():
    if not session.get("username"):
        return redirect(url_for("frontend.login"))
    if request.method == "POST":
        # Il form e' in secondi interi; l'API di Unity usa millisecondi.
        try:
            time_ms = int(request.form.get("seconds", "")) * 1000
            penalty_ms = int(request.form.get("penalty", "0")) * 1000
        except ValueError:
            flash("Inserisci numeri interi per tempo e penalita'.")
            return render_template("aggiungi.html")
        try:
            nickname = request.form.get("nickname", "")
            add_score(nickname, time_ms, penalty_ms)
            flash("Risultato aggiunto alla classifica!")
            return redirect(url_for("frontend.index"))
        except ValueError as error:
            flash(str(error))
    return render_template("aggiungi.html")

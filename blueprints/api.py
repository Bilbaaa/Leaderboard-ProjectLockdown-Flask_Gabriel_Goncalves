"""API JSON: in futuro Unity potra' inviare il tempo a fine partita."""
import hmac
from flask import Blueprint, current_app, jsonify, request

from db import add_score, get_scores

api = Blueprint("api", __name__, url_prefix="/api")


@api.get("/scores")
def load_all_scores():
    """Lettura libera della classifica."""
    return jsonify({"scores": get_scores()})


@api.post("/score")
def save_score():
    """Inserimento con un solo token segreto in .env (Bearer)."""
    expected = "Bearer " + current_app.config["API_TOKEN"]
    given = request.headers.get("Authorization", "")
    if not hmac.compare_digest(given, expected):
        return jsonify({"error": "Token mancante o non valido."}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Devi inviare un oggetto JSON."}), 400
    try:
        score_id = add_score(
            data.get("nickname"), data.get("time_ms"), data.get("penalty_ms", 0)
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"message": "Risultato salvato", "id": score_id}), 201

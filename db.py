import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import current_app
from werkzeug.security import generate_password_hash

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


@contextmanager
def open_db():
    """Apre, salva e chiude una connessione SQLite."""
    connection = sqlite3.connect(current_app.config["DB_PATH"])
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    """Applica le migrazioni ancora mancanti e crea due utenti locali."""
    Path(current_app.config["DB_PATH"]).parent.mkdir(parents=True, exist_ok=True)
    with open_db() as db:
        db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)")
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = migration.stem
            already = db.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?", (version,)
            ).fetchone()
            if not already:
                db.executescript(migration.read_text(encoding="utf-8"))
                db.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))

        for username, role, password_field in [
            ("player", "player", "PLAYER_PASSWORD"),
            ("admin", "admin", "ADMIN_PASSWORD"),
        ]:
            # Le password vengono salvate come hash, mai in chiaro nel database.
            db.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, generate_password_hash(current_app.config[password_field]), role),
            )


def validate_score(nickname, time_ms, penalty_ms):
    """Usata sia dal modulo web sia dall'API di Unity."""
    if not isinstance(nickname, str) or not (2 <= len(nickname.strip()) <= 24):
        raise ValueError("Il nickname deve avere da 2 a 24 caratteri.")
    if type(time_ms) is not int or type(penalty_ms) is not int:
        raise ValueError("Tempo e penalita' devono essere interi (millisecondi).")
    if time_ms <= 0 or penalty_ms < 0 or time_ms + penalty_ms > 600000:
        raise ValueError("Il tempo totale deve essere tra 1 ms e 10 minuti.")
    return nickname.strip(), time_ms, penalty_ms


def get_scores():
    """Restituisce i migliori 50 tempi, penalita' incluse."""
    with open_db() as db:
        rows = db.execute("""
            SELECT id, nickname, time_ms, penalty_ms,
                   time_ms + penalty_ms AS total_ms, created_at
            FROM scores ORDER BY total_ms ASC, id ASC LIMIT 50
        """).fetchall()
        return [dict(row) for row in rows]


def add_score(nickname, time_ms, penalty_ms):
    """Inserisce il risultato e restituisce il suo ID."""
    nickname, time_ms, penalty_ms = validate_score(nickname, time_ms, penalty_ms)
    with open_db() as db:
        cursor = db.execute(
            "INSERT INTO scores (nickname, time_ms, penalty_ms) VALUES (?, ?, ?)",
            (nickname, time_ms, penalty_ms),
        )
        return cursor.lastrowid


def format_time(milliseconds):
    """Esempio: 327450 -> 05:27.450."""
    minutes, remainder = divmod(milliseconds, 60000)
    seconds, millis = divmod(remainder, 1000)
    return f"{minutes:02}:{seconds:02}.{millis:03}"

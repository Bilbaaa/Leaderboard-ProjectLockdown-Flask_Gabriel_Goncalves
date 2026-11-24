"""Project Lockdown - demo Flask della classifica (Unity potra' usare l'API)."""
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from db import format_time, init_db
from blueprints.frontend import frontend
from blueprints.api import api
from blueprints.admin import admin

BASE_DIR = Path(__file__).resolve().parent


def create_app(test_config=None):
    """Crea Flask, collega blueprint e prepara il database."""
    load_dotenv(BASE_DIR / ".env")
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "chiave-solo-demo"),
        DB_PATH=os.getenv("DB_PATH", "instance/leaderboard.db"),
        API_TOKEN=os.getenv("API_TOKEN", "demo-token"),
        ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD", "admin123"),
        PLAYER_PASSWORD=os.getenv("PLAYER_PASSWORD", "player123"),
    )
    if test_config:
        app.config.update(test_config)

    # Un percorso relativo viene sempre cercato nella cartella del progetto.
    path = Path(app.config["DB_PATH"])
    if not path.is_absolute():
        path = BASE_DIR / path
    app.config["DB_PATH"] = str(path)

    app.jinja_env.filters["time"] = format_time
    app.register_blueprint(frontend)
    app.register_blueprint(api)
    app.register_blueprint(admin)

    with app.app_context():
        init_db()
    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host=os.getenv("HOST", "127.0.0.1"), port=5000, debug=False)

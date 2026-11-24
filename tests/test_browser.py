from threading import Thread
import pytest
from playwright.sync_api import expect
from werkzeug.serving import make_server
from app import create_app


@pytest.fixture
def server_url(tmp_path):
    app = create_app({"TESTING": True, "SECRET_KEY": "test-key",
                      "DB_PATH": str(tmp_path / "browser.db"),
                      "PLAYER_PASSWORD": "player123", "ADMIN_PASSWORD": "admin123"})
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)
    server.server_close()


def accedi(page, url, utente="player"):
    page.goto(url + "/login")
    page.get_by_label("Username").fill(utente)
    page.get_by_label("Password").fill(utente + "123")
    page.get_by_role("button", name="Accedi").click()


def aggiungi(page, nome):
    page.get_by_role("link", name="Aggiungi tempo").click()
    page.get_by_label("Nickname del giocatore").fill(nome)
    page.get_by_label("Tempo impiegato (secondi)").fill("312")
    page.get_by_label("Penalità (secondi)").fill("15")
    page.get_by_role("button", name="Salva risultato").click()


def test_login(page, server_url):
    accedi(page, server_url)
    expect(page.get_by_role("link", name="Aggiungi tempo")).to_be_visible()


def test_aggiungi_tempo(page, server_url):
    accedi(page, server_url)
    aggiungi(page, "MarioPW")
    expect(page.locator("tbody tr").filter(has_text="MarioPW")).to_contain_text("05:27.000")


def test_admin_elimina(page, server_url):
    accedi(page, server_url, "admin")
    aggiungi(page, "ProvaAdmin")
    page.get_by_role("link", name="Admin", exact=True).click()
    page.locator("tbody tr").filter(has_text="ProvaAdmin").get_by_role(
        "button", name="Elimina").click()
    expect(page.get_by_text("Non ci sono risultati da eliminare.")).to_be_visible()

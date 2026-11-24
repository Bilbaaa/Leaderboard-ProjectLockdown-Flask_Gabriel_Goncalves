"""Test semplici per pagine, API e database con pytest."""
import sqlite3
import pytest
from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True, "SECRET_KEY": "test-key",
        "DB_PATH": str(tmp_path / "test.db"), "API_TOKEN": "test-token",
        "PLAYER_PASSWORD": "player123", "ADMIN_PASSWORD": "admin123",
    })


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, user="player"):
    return client.post("/login", data={"username": user, "password": user + "123"})


def invia_tempo(client, nome="Mario", tempo=210000, penalita=0):
    return client.post("/api/score", json={
        "nickname": nome, "time_ms": tempo, "penalty_ms": penalita,
    }, headers={"Authorization": "Bearer test-token"})


# Test delle pagine HTML e dei permessi

def test_pagine_pubbliche(client):
    assert b"Classifica" in client.get("/").data
    assert b"Username" in client.get("/login").data
    assert client.get("/aggiungi").status_code == 302
    assert client.get("/admin/").status_code == 302


def test_login_logout(client):
    assert b"errati" in client.post("/login", data={
        "username": "player", "password": "sbagliata",
    }).data
    assert login(client).status_code == 302
    assert client.get("/aggiungi").status_code == 200
    assert client.post("/logout").status_code == 302
    assert client.get("/aggiungi").status_code == 302


def test_permessi_admin(client):
    login(client)
    assert client.get("/admin/").status_code == 403
    assert client.post("/admin/elimina/1").status_code == 403
    client.post("/logout")
    login(client, "admin")
    assert b"Gestione risultati" in client.get("/admin/").data


def test_form_errato(client):
    login(client)
    risposta = client.post("/aggiungi", data={
        "nickname": "Mario", "seconds": "abc", "penalty": "0",
    })
    assert b"numeri interi" in risposta.data


# Test delle API JSON

def test_api_senza_token(client):
    assert client.post("/api/score", json={"nickname": "Mario"}).status_code == 401
    assert client.get("/api/scores").get_json() == {"scores": []}


@pytest.mark.parametrize("dati", [
    {"nickname": "A", "time_ms": 1000},
    {"nickname": "Mario", "time_ms": -1},
    {"nickname": "Mario", "time_ms": "1000"},
    {"nickname": "Mario", "time_ms": 590000, "penalty_ms": 30000},
])
def test_api_dati_errati(client, dati):
    risposta = client.post("/api/score", json=dati,
                           headers={"Authorization": "Bearer test-token"})
    assert risposta.status_code == 400


# Tre test di integrazione: passaggi completi fra API, web e database

def test_integrazione_api_classifica(client):
    assert invia_tempo(client, "UnityDemo", 312000, 15000).status_code == 201
    risultato = client.get("/api/scores").get_json()["scores"][0]
    assert risultato["total_ms"] == 327000
    assert b"UnityDemo" in client.get("/").data
    assert b"05:27.000" in client.get("/").data


def test_integrazione_form_classifica(client):
    login(client)
    risposta = client.post("/aggiungi", data={
        "nickname": "Giulia", "seconds": "245", "penalty": "10",
    })
    assert risposta.status_code == 302
    assert client.get("/api/scores").get_json()["scores"][0]["total_ms"] == 255000


def test_integrazione_eliminazione_admin(client):
    risultato_id = invia_tempo(client).get_json()["id"]
    login(client, "admin")
    assert client.post(f"/admin/elimina/{risultato_id}").status_code == 302
    assert client.get("/api/scores").get_json()["scores"] == []


def test_ordinamento_e_migrazione(client, app):
    invia_tempo(client, "Veloce", 180000, 90000)
    invia_tempo(client, "Costante", 240000)
    risultati = client.get("/api/scores").get_json()["scores"]
    assert [r["nickname"] for r in risultati] == ["Costante", "Veloce"]
    with sqlite3.connect(app.config["DB_PATH"]) as db:
        assert db.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1

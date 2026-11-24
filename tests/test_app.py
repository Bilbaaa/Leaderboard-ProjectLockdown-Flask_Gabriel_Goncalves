
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



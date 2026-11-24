-- Migrazione 001: crea le tabelle soltanto se non esistono.
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'player'))
);

CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nickname TEXT NOT NULL,
    time_ms INTEGER NOT NULL CHECK (time_ms > 0),
    penalty_ms INTEGER NOT NULL DEFAULT 0 CHECK (penalty_ms >= 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

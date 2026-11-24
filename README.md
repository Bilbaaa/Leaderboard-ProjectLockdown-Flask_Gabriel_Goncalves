[README.md](https://github.com/user-attachments/files/35339824/README.md)
# Project Lockdown - Leaderboard

Questo progetto l'ho realizzato per il laboratorio di Flask, partendo dalla bozza **Leaderboard** iniziata in classe.

L'idea è fare una classifica per **Project Lockdown**, la mia escape room in realtà virtuale che sto sviluppando con Unity per Meta Quest 3. La parte del gioco non è ancora finita, quindi per adesso posso inserire dei tempi di prova dal sito oppure mandarli tramite API. Quando finirò il gioco, i risultati potranno arrivare direttamente da Unity.

## Cosa si può fare

- Vedere una classifica con i **50 tempi migliori**, dal più basso al più alto.
- Inserire un nickname, un tempo e un'eventuale penalità.
- Salvare i risultati in un database SQLite, così rimangono anche quando chiudo il programma.
- Accedere con due utenti: `player` e `admin`. Il player può aggiungere tempi e l'admin può anche eliminarli.
- Usare un'API per leggere la classifica o aggiungere un risultato senza passare dal sito.

Il tempo totale è **tempo impiegato + penalità**. Nel database i tempi sono in millisecondi, mentre sul sito vengono mostrati per esempio come `05:27.000`.

## Come avviare il progetto

Ho usato Python e Flask. Per avviarlo su Windows apro la cartella in VS Code e dal terminale PowerShell, nella cartella dove c'è `app.py`, eseguo:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env-example .env
.\.venv\Scripts\python.exe app.py
```

Poi apro **http://127.0.0.1:5000**.

I primi tre comandi servono solo alla prima configurazione. Le volte successive, se non ho cambiato niente, basta avviare `app.py` con l'ultimo comando.

Per provare il login ci sono questi due account:

| Utente | Password iniziale | Cosa può fare |
| --- | --- | --- |
| `player` | `player123` | Aggiungere tempi |
| `admin` | `admin123` | Aggiungere ed eliminare tempi |

Per esempio posso entrare come player, andare su **Aggiungi tempo** e inserire `Mario`, `312` secondi e `15` secondi di penalità. Nella classifica comparirà `05:27.000`.

## Database e utenti

Ho scelto **SQLite** perché per un progetto di queste dimensioni non mi serve installare un server MySQL. I dati vengono salvati nel file `instance/leaderboard.db`.

Nel database ci sono queste tabelle:

- `users`: contiene username, password sotto forma di hash e ruolo.
- `scores`: contiene nickname, tempo, penalità e data del risultato.
- `schema_migrations`: tiene traccia delle migrazioni già eseguite.

Gli account `player` e `admin` vengono creati dal codice in `db.py` al primo avvio. Le password iniziali sono lette dal file `.env` e nel database non vengono salvate in chiaro, ma come hash.

Per creare le tabelle uso la migrazione `migrations/001_init.sql`. Viene eseguita solo se non è già stata applicata. Se riavvio Flask, quindi, i risultati non spariscono.

**Nota:** se cambio le password nel `.env` dopo il primo avvio, quelle degli utenti già creati non cambiano automaticamente. Per ricominciare da zero in locale posso eliminare `instance/leaderboard.db` con Flask spento, ma così perdo anche tutti i risultati.

## Login e permessi

Il sito usa le **sessioni di Flask** per ricordare chi ha fatto il login.

La classifica è visibile a tutti, anche senza account. Per aggiungere un tempo dal sito bisogna essere collegati. Solo l'admin può entrare nel pannello di gestione ed eliminare i risultati.

I controlli dei permessi sono nel codice Python, non soltanto nei pulsanti della pagina.

## API (per il futuro collegamento con Unity)

Ho preparato due indirizzi:

| Metodo | Indirizzo | A cosa serve |
| --- | --- | --- |
| `GET` | `/api/scores` | Restituisce la classifica in JSON |
| `POST` | `/api/score` | Aggiunge un risultato |

La richiesta `GET` è pubblica. Per la `POST` bisogna inviare un **Bearer Token**, cioè una chiave scritta nel file `.env`. Non è un JWT: è solo un token fisso, sufficiente per questa demo locale.

Un esempio di richiesta POST è:

```http
POST http://127.0.0.1:5000/api/score
Content-Type: application/json
Authorization: Bearer token-di-prova-123
```

Con questo JSON:

```json
{
  "nickname": "UnityDemo",
  "time_ms": 312000,
  "penalty_ms": 15000
}
```

Il totale è **327000 ms**, cioè `05:27.000`. Se i dati sono corretti Flask salva il risultato e risponde con `201`. Senza token corretto risponde con `401`, mentre con dati non validi risponde con `400`.

Per fare delle prove c'è anche `test.http`, utilizzabile in VS Code con l'estensione **REST Client**. Se cambio il token nel `.env`, devo cambiarlo anche nelle richieste di prova.

### Collegamento con Unity

Quando avrò finito l'escape room, dovrò creare uno script C# che alla fine della partita recupera nickname, tempo impiegato e penalità e li invia a Flask con `UnityWebRequest`.

Se provo Unity sullo stesso PC posso usare `127.0.0.1`. Se invece il gioco gira direttamente sul Meta Quest, dovrò usare l'IP del PC su cui gira Flask, tenere i dispositivi sulla stessa rete e configurare l'accesso dalla rete locale (per esempio `HOST=0.0.0.0`). Per adesso il collegamento con Unity non è ancora stato fatto.

## Test

Ho usato i metodi visti nella Lezione 6: **pytest** e **Playwright**.

In `tests/test_app.py` ci sono test per le pagine, il login, i permessi, l'API e il database, compresi tre test di integrazione. In `tests/test_browser.py` ci sono tre test Playwright che aprono Chromium e provano il login, l'aggiunta di un tempo e l'eliminazione come admin.

Per installare Chromium la prima volta:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

Per eseguire tutti i test:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Per vedere Playwright usare il browser:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_browser.py --headed -v
```

Per controllare la copertura del codice:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=app --cov=blueprints --cov=db --cov-report=term-missing
```

I test usano database temporanei, quindi non modificano la classifica normale. La copertura effettiva va controllata eseguendo l'ultimo comando; nella lezione l'obiettivo indicato è l'80%.

## I file principali

```text
Project_Lockdown_Leaderboard/
├── app.py                   # Avvio e configurazione di Flask
├── db.py                    # Database e gestione dei risultati
├── blueprints/
│   ├── frontend.py          # Pagine, login e aggiunta tempi
│   ├── api.py               # API JSON
│   └── admin.py             # Pannello admin
├── templates/               # Pagine HTML
├── static/style.css         # Stile del sito
├── migrations/001_init.sql  # Creazione delle tabelle
├── tests/
│   ├── test_app.py          # Test pytest
│   └── test_browser.py      # Test Playwright
├── .env-example             # Esempio di configurazione
├── .gitignore               # File da escludere da Git
├── requirements.txt         # Librerie Python
├── test.http                # Prove delle API
├── Dockerfile
└── compose.yaml
```

### File `.env` e `.gitignore`

Il file `.env` contiene la chiave per la sessione (`SECRET_KEY`), il percorso del database (`DB_PATH`), le password iniziali (`PLAYER_PASSWORD` e `ADMIN_PASSWORD`) e il token dell'API (`API_TOKEN`).

Ho messo `.env-example` nel progetto per far vedere quali variabili servono. Il vero `.env` non va caricato su GitHub, così come il database locale e la cartella `.venv`. Questi file vengono esclusi tramite `.gitignore`.

## Docker (facoltativo)

Ho lasciato anche `Dockerfile` e `compose.yaml` perché Docker è stato trattato nella Lezione 6. Servono ad avviare Flask in un container, senza configurare Python direttamente sul computer.

Se ho Docker Desktop e ho già creato il file `.env`, posso usare:

```powershell
docker compose up --build
```

Per fermarlo:

```powershell
docker compose down
```

Non ho aggiunto un container MySQL perché uso SQLite. Il database rimane nella cartella `instance`. Per il laboratorio posso comunque avviare tutto normalmente con Python, senza Docker.


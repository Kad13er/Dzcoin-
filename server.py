"""Serveur Dzcoin : API des points + sert la Mini App. Lancer : uvicorn server:app --host 0.0.0.0 --port 8000"""
import hashlib, hmac, json, os, sqlite3, time
from datetime import date
from urllib.parse import parse_qsl
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

BOT_TOKEN = os.environ["BOT_TOKEN"]
DB_PATH = os.environ.get("DB_PATH", "dzcoin.db")
MAX_ENERGY = 500      # énergie max
REGEN = 1.0           # énergie récupérée par seconde
MAX_TAPS_PER_CALL = 25
AD_BONUS = 200        # énergie rendue après une pub
AD_DAILY_LIMIT = 10   # pubs max par jour et par utilisateur
AD_COOLDOWN = 30      # secondes entre deux pubs

app = FastAPI()

def db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

with db() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY, name TEXT, points INTEGER DEFAULT 0,
        energy REAL DEFAULT 500, updated REAL, ad_day TEXT DEFAULT '',
        ad_count INTEGER DEFAULT 0, last_ad REAL DEFAULT 0)""")

def verify(init_data: str) -> dict:
    """Vérifie que les données viennent bien de Telegram (signature HMAC)."""
    try:
        data = dict(parse_qsl(init_data, keep_blank_values=True))
        received = data.pop("hash")
        check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, received):
            raise ValueError
        if time.time() - int(data["auth_date"]) > 86400:
            raise ValueError
        return json.loads(data["user"])
    except Exception:
        raise HTTPException(401, "Non autorisé")

def load(conn, tg):
    now = time.time()
    row = conn.execute("SELECT * FROM users WHERE id=?", (tg["id"],)).fetchone()
    if not row:
        conn.execute("INSERT INTO users(id,name,energy,updated) VALUES(?,?,?,?)",
                     (tg["id"], tg.get("first_name", "Joueur"), MAX_ENERGY, now))
        row = conn.execute("SELECT * FROM users WHERE id=?", (tg["id"],)).fetchone()
    energy = min(MAX_ENERGY, row["energy"] + (now - row["updated"]) * REGEN)
    return row, energy, now

def state(row, energy, ads_left):
    return {"points": row["points"], "energy": int(energy), "max_energy": MAX_ENERGY, "ads_left": ads_left}

def ads_left(row):
    return AD_DAILY_LIMIT - (row["ad_count"] if row["ad_day"] == str(date.today()) else 0)

class Taps(BaseModel):
    taps: int

@app.post("/api/state")
def get_state(x_init_data: str = Header()):
    tg = verify(x_init_data)
    with db() as c:
        row, energy, now = load(c, tg)
        c.execute("UPDATE users SET energy=?, updated=? WHERE id=?", (energy, now, tg["id"]))
        return state(row, energy, ads_left(row))

@app.post("/api/tap")
def tap(body: Taps, x_init_data: str = Header()):
    tg = verify(x_init_data)
    n = max(0, min(body.taps, MAX_TAPS_PER_CALL))
    with db() as c:
        row, energy, now = load(c, tg)
        n = min(n, int(energy))
        energy -= n
        c.execute("UPDATE users SET points=points+?, energy=?, updated=? WHERE id=?", (n, energy, now, tg["id"]))
        row = c.execute("SELECT * FROM users WHERE id=?", (tg["id"],)).fetchone()
        return state(row, energy, ads_left(row))

@app.post("/api/ad")
def ad_reward(x_init_data: str = Header()):
    """Appelé après qu'une pub récompensée a été regardée en entier."""
    tg = verify(x_init_data)
    today = str(date.today())
    with db() as c:
        row, energy, now = load(c, tg)
        count = row["ad_count"] if row["ad_day"] == today else 0
        if count >= AD_DAILY_LIMIT or now - row["last_ad"] < AD_COOLDOWN:
            raise HTTPException(429, "Limite de pubs atteinte, réessaie plus tard")
        energy = min(MAX_ENERGY, energy + AD_BONUS)
        c.execute("UPDATE users SET energy=?, updated=?, ad_day=?, ad_count=?, last_ad=? WHERE id=?",
                  (energy, now, today, count + 1, now, tg["id"]))
        row = c.execute("SELECT * FROM users WHERE id=?", (tg["id"],)).fetchone()
        return state(row, energy, ads_left(row))

@app.get("/api/top")
def top():
    with db() as c:
        rows = c.execute("SELECT name, points FROM users ORDER BY points DESC LIMIT 10").fetchall()
        return [{"name": r["name"], "points": r["points"]} for r in rows]

@app.get("/")
def index():
    return FileResponse("static/index.html")

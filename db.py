"""SQLite storage for CyberShield: users, complaints, recovery progress, status updates, scam alerts."""
import datetime as dt, hashlib, json, os, secrets, sqlite3, uuid
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "cybershield.db"
SCHEMA = """
create table if not exists users(id integer primary key, username text unique, salt text, pw text, role text default 'user');
create table if not exists complaints(cid text primary key, user_id integer, attack text, incidents text, system text,
  description text, contact text, evidence text, facts text, plan text, severity text, status text default 'Submitted',
  investigator text default '', created text, closed text);
create table if not exists progress(cid text, action_id text, done_at text, primary key(cid, action_id));
create table if not exists events(id integer primary key, cid text, at text, note text);
create table if not exists alerts(id integer primary key, at text, title text, body text);
"""
now = lambda: dt.datetime.now().isoformat(timespec="seconds")


def conn():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.executescript(SCHEMA)
        has_admin = c.execute("select 1 from users where role='admin'").fetchone()
    if not has_admin:   # change this password after first login (or set CYBERSHIELD_ADMIN_PW)
        register("admin", os.environ.get("CYBERSHIELD_ADMIN_PW", "admin123"), "admin")


def _hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()


def register(username, pw, role="user"):
    if len(username) < 3 or len(pw) < 6:
        raise ValueError("Username needs 3+ characters and password 6+.")
    salt = secrets.token_hex(16)
    try:
        with conn() as c:
            c.execute("insert into users(username,salt,pw,role) values(?,?,?,?)", (username, salt, _hash(pw, salt), role))
    except sqlite3.IntegrityError:
        raise ValueError("That username is taken.")


def login(username, pw):
    with conn() as c:
        r = c.execute("select * from users where username=?", (username,)).fetchone()
    return dict(r) if r and secrets.compare_digest(r["pw"], _hash(pw, r["salt"])) else None


def suggest_severity(facts, incidents):
    if facts.get("money") or facts.get("paid") or facts.get("docs") or "rw" in incidents:
        return "High"
    if facts.get("cred") or facts.get("otp") or facts.get("work") or len(incidents) > 1:
        return "Medium"
    return "Low"


def event(cid, note):
    with conn() as c:
        c.execute("insert into events(cid,at,note) values(?,?,?)", (cid, now(), note))


def create_complaint(user_id, attack, incidents, system, description, contact, evidence, facts, plan, severity):
    cid = f"CS-{dt.date.today():%Y%m%d}-{uuid.uuid4().hex[:4].upper()}"
    with conn() as c:
        c.execute("insert into complaints(cid,user_id,attack,incidents,system,description,contact,evidence,facts,plan,severity,created)"
                  " values(?,?,?,?,?,?,?,?,?,?,?,?)", (cid, user_id, attack, json.dumps(incidents), system, description, contact,
                                                      evidence, json.dumps(facts), json.dumps(plan), severity, now()))
    event(cid, "Complaint registered. Your recovery plan is ready.")
    return cid


def complaints(user_id=None, q="", status=""):
    sql, args = "select complaints.*, users.username as username from complaints left join users on users.id=complaints.user_id where 1=1", []
    if user_id:
        sql += " and user_id=?"; args.append(user_id)
    if status:
        sql += " and status=?"; args.append(status)
    if q:
        sql += " and (cid like ? or attack like ? or description like ? or investigator like ?)"; args += [f"%{q}%"] * 4
    with conn() as c:
        return [dict(r) for r in c.execute(sql + " order by created desc", args)]


def get(cid):
    with conn() as c:
        r = c.execute("select * from complaints where cid=?", (cid,)).fetchone()
    return dict(r) if r else None


def set_action(cid, action_id, done):
    with conn() as c:
        if done:
            c.execute("insert or ignore into progress values(?,?,?)", (cid, action_id, now()))
        else:
            c.execute("delete from progress where cid=? and action_id=?", (cid, action_id))


def done(cid):
    with conn() as c:
        return {r[0] for r in c.execute("select action_id from progress where cid=?", (cid,))}


def update(cid, status, severity, investigator, note=""):
    with conn() as c:
        c.execute("update complaints set status=?, severity=?, investigator=?, closed=? where cid=?",
                  (status, severity, investigator, now() if status == "Closed" else None, cid))
    event(cid, f"Status: {status}. Severity: {severity}." + (f" {note}" if note else ""))


def events(cid):
    with conn() as c:
        return [dict(r) for r in c.execute("select * from events where cid=? order by id desc", (cid,))]


def add_alert(title, body):
    with conn() as c:
        c.execute("insert into alerts(at,title,body) values(?,?,?)", (now(), title, body))


def alerts():
    with conn() as c:
        return [dict(r) for r in c.execute("select * from alerts order by id desc")]


def overview():
    rows = []
    for c in complaints():
        plan = json.loads(c["plan"])
        rows.append({"cid": c["cid"], "attack": c["attack"], "severity": c["severity"], "status": c["status"],
                     "investigator": c["investigator"], "created": c["created"],
                     "recovery_pct": round(100 * len(done(c["cid"]) & set(plan)) / max(len(plan), 1))})
    return pd.DataFrame(rows, columns=["cid", "attack", "severity", "status", "investigator", "created", "recovery_pct"])

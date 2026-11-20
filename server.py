"""CyberShield web app. No extra installs needed.
Run:  python server.py     then open http://127.0.0.1:8000   (first admin login: admin / admin123)"""
import base64, json, os, random, re, secrets, sys, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import mimetypes
import pandas as pd
import db
from library import INCIDENTS, FACTS, INCIDENT_FACTS, BY_ID, essential
from engines import ENGINES
from attacks import ATTACKS, TIPS, FINAL_CHECK
from experiment import make_scenario, score

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)                       # keeps data/ next to the code, same as the Streamlit version
SYSTEM = "C: Intelligent"
STATUSES = ["Submitted", "Under review", "Investigating", "Resolved", "Closed"]
LEVELS = ["Low", "Medium", "High"]
NAMES = list(ENGINES)
ORDERS = [[0, 1, 2], [1, 2, 0], [2, 0, 1]]                         # cyclic Latin square of systems
SCEN = [make_scenario(random.Random(100 + k)) for k in range(3)]   # same three fictional cases for everyone
LOG, EVID = Path("data/study_log.csv"), Path("data/evidence")
SESS = {}


def steps_of(c):
    plat = ATTACKS.get(c["attack"], ("", "", 0))[1] or "the platform"
    done = db.done(c["cid"])
    return [{"id": i, "text": BY_ID[i].text.replace("the platform", plat), "why": BY_ID[i].why,
             "urg": BY_ID[i].urg, "done": i in done} for i in json.loads(c["plan"])]


def progress(c):
    s = steps_of(c)
    n = sum(x["done"] for x in s)
    return n, len(s), round(100 * n / max(len(s), 1))


def summary(c):
    n, t, p = progress(c)
    out = {k: c[k] for k in ("cid", "attack", "severity", "status", "investigator", "created")} | {"done": n, "total": t, "pct": p}
    if c.get("username"):
        out["reported_by"] = c["username"]
    return out


def detail(c, admin):
    n, t, p = progress(c)
    d = summary(c) | {"description": c["description"], "contact": c["contact"], "steps": steps_of(c),
                      "events": db.events(c["cid"]), "evidence": c["evidence"].split("_", 1)[-1] if c["evidence"] else ""}
    if admin:
        d["facts"] = {FACTS[f]: v for f, v in json.loads(c["facts"]).items() if f in FACTS}
    return d


def study_ctx(pid, k):
    if not pid or not 0 <= k < 3:
        raise ValueError("Enter a participant ID.")
    I, c = SCEN[k]
    return I, c, NAMES[ORDERS[sum(map(ord, pid)) % 3][k]]


def meta():
    return {"incidents": INCIDENTS, "facts": FACTS, "incidentFacts": INCIDENT_FACTS, "attacks": ATTACKS,
            "tips": TIPS, "finalCheck": FINAL_CHECK, "statuses": STATUSES, "levels": LEVELS}


def clean(o):
    """JSON has no NaN: turn missing numbers into null so the browser can read the response."""
    if isinstance(o, float) and (o != o or o in (float("inf"), float("-inf"))):
        return None
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    return o


class Err(Exception):
    def __init__(self, code, msg):
        self.code, self.msg = code, msg


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, body, code=200, ctype="application/json", extra=()):
        if not isinstance(body, bytes):
            body = json.dumps(clean(body), default=str).encode()
        self.send_response(code)
        for k, v in (("Content-Type", ctype), ("Content-Length", str(len(body))), ("Cache-Control", "no-store"),
                     ("X-Content-Type-Options", "nosniff"), *extra):
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.go("GET")

    def do_POST(self):
        self.go("POST")

    def go(self, method):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            body = {}
            if method == "POST":
                n = int(self.headers.get("Content-Length") or 0)
                if n > 8_000_000:
                    raise Err(413, "That upload is too large.")
                body = json.loads(self.rfile.read(n) or b"{}")
            if u.path == "/":
                return self.send((ROOT / "web" / "index.html").read_bytes(), ctype="text/html; charset=utf-8")
            if not u.path.startswith("/api/"):
                raise Err(404, "Not found")
            self.api(method, u.path[5:], q, body)
        except Err as e:
            self.send({"error": e.msg}, e.code)
        except ValueError as e:
            self.send({"error": str(e)}, 400)
        except Exception as e:          # never leak a traceback to the browser
            print("error:", repr(e), file=sys.stderr)
            self.send({"error": "Something went wrong on the server."}, 500)

    def api(self, method, name, q, b):
        m = re.search(r"cs=([\w-]+)", self.headers.get("Cookie", ""))
        u = SESS.get(m.group(1)) if m else None
        if name == "meta":
            return self.send(meta())
        if name == "me":
            return self.send({"user": u and {"username": u["username"], "role": u["role"]}})
        if name == "register" and method == "POST":
            db.register(str(b.get("username", "")).strip(), str(b.get("password", "")))
            return self.send({"ok": True})
        if name == "login" and method == "POST":
            usr = db.login(str(b.get("username", "")).strip(), str(b.get("password", "")))
            if not usr:
                raise Err(401, "Wrong username or password.")
            tok = secrets.token_urlsafe(24)
            SESS[tok] = {"id": usr["id"], "username": usr["username"], "role": usr["role"]}
            return self.send({"ok": True}, extra=[("Set-Cookie", f"cs={tok}; HttpOnly; SameSite=Lax; Path=/")])
        if name == "logout" and method == "POST":
            if m:
                SESS.pop(m.group(1), None)
            return self.send({"ok": True}, extra=[("Set-Cookie", "cs=; Max-Age=0; Path=/")])
        if not u:
            raise Err(401, "Please sign in.")
        admin = u["role"] == "admin"

        def own(cid):
            c = db.get(cid)
            if not c or not (admin or c["user_id"] == u["id"]):
                raise Err(404, "Complaint not found.")
            return c

        def need_admin():
            if not admin:
                raise Err(403, "Administrators only.")

        if name == "complaints":
            rows = db.complaints(None if admin else u["id"], q.get("q", ""), q.get("status", ""))
            if admin:
                rank = {"High": 0, "Medium": 1, "Low": 2}
                rows.sort(key=lambda c: (rank.get(c["severity"], 3), c["created"]))
            return self.send([summary(c) for c in rows])
        if name.startswith("complaint/"):
            return self.send(detail(own(name[10:]), admin))
        if name == "report" and method == "POST":
            attack = b.get("attack")
            if attack not in ATTACKS:
                raise ValueError("Choose an attack type.")
            code = ATTACKS[attack][0]
            also = [i for i in b.get("also", []) if i in INCIDENTS and i != code]
            incs = [code] + also
            allowed = {f for i in incs for f in INCIDENT_FACTS[i]}
            obs = {f: bool(v) for f, v in (b.get("facts") or {}).items() if f in allowed and v is not None}
            desc = str(b.get("description", "")).strip()[:4000]
            if not desc:
                raise ValueError("Add a short description so an investigator can follow up.")
            sev = b.get("severity") if b.get("severity") in LEVELS else db.suggest_severity(obs, incs)
            plan = [a.id for a, _ in ENGINES[SYSTEM](incs, obs)]
            when = str(b.get("when") or "")[:10]
            cid = db.create_complaint(u["id"], attack, incs, SYSTEM, f"[{when}] {desc}" if when else desc,
                                      str(b.get("contact", ""))[:200], "", obs, plan, sev)
            ev = b.get("evidence")
            if ev and ev.get("data"):
                raw = base64.b64decode(ev["data"])
                if len(raw) > 5_000_000:
                    raise ValueError("Evidence must be under 5 MB.")
                EVID.mkdir(parents=True, exist_ok=True)
                path = EVID / f"{cid}_{re.sub(r'[^A-Za-z0-9.-]', '-', Path(str(ev.get('name', 'file'))).name)[:80]}"
                path.write_bytes(raw)
                with db.conn() as cn:
                    cn.execute("update complaints set evidence=? where cid=?", (str(path), cid))
            return self.send({"cid": cid})
        if name == "action" and method == "POST":
            c = db.get(str(b.get("cid")))
            if not c or c["user_id"] != u["id"] or b.get("action") not in json.loads(c["plan"]):
                raise Err(404, "Complaint not found.")
            db.set_action(c["cid"], b["action"], bool(b.get("done")))
            n, t, p = progress(c)
            return self.send({"done": n, "total": t, "pct": p})
        if name.startswith("evidence/"):
            c = own(name[9:])
            if not c["evidence"] or not Path(c["evidence"]).exists():
                raise Err(404, "No evidence attached.")
            fn = c["evidence"].split("_", 1)[-1]
            return self.send(Path(c["evidence"]).read_bytes(), ctype=mimetypes.guess_type(fn)[0] or "application/octet-stream",
                             extra=[("Content-Disposition", f'attachment; filename="{fn}"')])
        if name == "alerts" and method == "GET":
            return self.send(db.alerts())
        if name == "alerts" and method == "POST":
            need_admin()
            t, body = str(b.get("title", "")).strip()[:120], str(b.get("body", "")).strip()[:1000]
            if not t or not body:
                raise ValueError("Add a title and a message.")
            db.add_alert(t, body)
            return self.send({"ok": True})
        if name == "admin/update" and method == "POST":
            need_admin()
            if not db.get(str(b.get("cid"))) or b.get("status") not in STATUSES or b.get("severity") not in LEVELS:
                raise ValueError("Invalid update.")
            db.update(b["cid"], b["status"], b["severity"], str(b.get("investigator", ""))[:80], str(b.get("note", ""))[:300])
            return self.send({"ok": True})
        if name == "admin/analytics":
            need_admin()
            df = db.overview()
            if df.empty:
                return self.send({"total": 0, "closed": 0, "avg": 0, "attack": {}, "severity": {}, "status": {}})
            return self.send({"total": len(df), "closed": int(df.status.isin(["Resolved", "Closed"]).sum()),
                              "avg": round(float(df.recovery_pct.mean())), "attack": df.attack.value_counts().to_dict(),
                              "severity": df.severity.value_counts().to_dict(), "status": df.status.value_counts().to_dict()})
        if name == "admin/export.csv":
            need_admin()
            return self.send(db.overview().to_csv(index=False).encode(), ctype="text/csv",
                             extra=[("Content-Disposition", 'attachment; filename="cybershield_report.csv"')])
        if name == "study/case":
            need_admin()
            k = int(q.get("k", 0))
            I, c, sysname = study_ctx(q.get("pid", "").strip(), k)
            fl = list(dict.fromkeys(f for i in I for f in INCIDENT_FACTS[i]))
            return self.send({"k": k, "system": sysname, "ask": sysname != NAMES[0], "incidents": [INCIDENTS[i] for i in I],
                              "facts": [{"id": f, "label": FACTS[f], "value": c[f]} for f in fl]})
        if name == "study/guidance" and method == "POST":
            need_admin()
            I, c, sysname = study_ctx(str(b.get("pid", "")).strip(), int(b.get("k", 0)))
            obs = {} if sysname == NAMES[0] else {f: bool(v) for f, v in (b.get("obs") or {}).items() if f in FACTS and v is not None}
            return self.send([{"id": a.id, "text": a.text, "why": a.why, "urg": a.urg} for a, _ in ENGINES[sysname](I, obs)])
        if name == "study/submit" and method == "POST":
            need_admin()
            pid, k = str(b.get("pid", "")).strip(), int(b.get("k", 0))
            I, c, sysname = study_ctx(pid, k)
            chosen = [i for i in b.get("chosen", []) if i in BY_ID]
            need = essential(I, c)
            hits = [float(t) for i, t in b.get("ticks", []) if i in chosen and i in need and BY_ID[i].urg >= 4]
            m = score([(BY_ID[i], None) for i in chosen], I, c)
            row = {"participant": pid, "case": k + 1, "system": sysname, "sec_to_first_correct_urgent": min(hits) if hits else None,
                   "sec_total": round(float(b.get("sec_total", 0)), 1), "selected": ";".join(chosen),
                   "correctness": m["correctness"], "completeness": m["completeness"], "unnecessary": m["unnecessary"],
                   "understanding": min(7, max(1, int(b.get("understanding", 4)))), "confidence": min(7, max(1, int(b.get("confidence", 4))))}
            LOG.parent.mkdir(exist_ok=True)
            pd.DataFrame([row]).to_csv(LOG, mode="a", header=not LOG.exists(), index=False)
            return self.send({"ok": True})
        if name == "study/results":
            need_admin()
            cols = ["sec_to_first_correct_urgent", "sec_total", "correctness", "completeness", "unnecessary", "understanding", "confidence"]
            out = {"study": None, "sim": None}
            if LOG.exists():
                df = pd.read_csv(LOG)
                out["study"] = {"participants": int(df.participant.nunique()), "rows": df.groupby("system")[cols].mean().round(2).reset_index().to_dict("records")}
            if Path("sim_results.csv").exists():
                s = pd.read_csv("sim_results.csv")
                out["sim"] = s.groupby("system")[["correctness", "completeness", "unnecessary", "est_seconds"]].mean().round(2).reset_index().to_dict("records")
            return self.send(out)
        raise Err(404, "Not found")



def main():
    db.init()

    # Render provides the PORT environment variable
    port = int(os.environ.get("PORT", 8000))

    # Listen on all network interfaces
    srv = ThreadingHTTPServer(("0.0.0.0", port), H)

    print(f"CyberShield is running on port {port}")

    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()

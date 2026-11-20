"""CyberShield. Run:  streamlit run app.py   (first admin login: admin / admin123, change it)"""
import json
from pathlib import Path
import pandas as pd
import streamlit as st
import db, study, style
from library import INCIDENTS, BY_ID
from engines import ENGINES
from attacks import ATTACKS, TIPS, FINAL_CHECK

SYSTEM = "C: Intelligent"
STATUSES = ["Submitted", "Under review", "Investigating", "Resolved", "Closed"]
LEVELS = ["Low", "Medium", "High"]
db.init()
st.set_page_config(page_title="CyberShield", page_icon="🛡️")
style.inject()


def pct_done(c):
    plan = json.loads(c["plan"])
    return len(db.done(c["cid"]) & set(plan)), len(plan)


def recovery(c, key=""):
    cid, plan = c["cid"], json.loads(c["plan"])
    plat = ATTACKS.get(c["attack"], ("", "", 0))[1] or "the platform"
    done = db.done(cid)
    st.subheader(f"Recovery plan {cid}")
    st.markdown(f"**{c['attack']}** {style.badge(c['status'], '#38BDF8')}{style.badge(c['severity'] + ' severity', style.SEV[c['severity']])}", unsafe_allow_html=True)
    st.caption("Hover a step’s ? for why it matters.")
    for i in plan:
        a = BY_ID[i]
        v = st.checkbox(a.text.replace("the platform", plat), value=i in done, key=f"{key}{cid}_{i}", help=a.why)
        if v != (i in done):
            db.set_action(cid, i, v)
    n, total = pct_done(c)
    pct = round(100 * n / max(total, 1))
    if pct == 100 and not st.session_state.get(f"cele_{cid}"):
        st.session_state[f"cele_{cid}"] = True
        st.balloons()
    m = st.columns(4)
    m[0].metric("Completed", n); m[1].metric("Pending", total - n); m[2].metric("Recovery", f"{pct}%")
    st.progress(pct / 100)
    with st.expander("Final security check"):
        chk = [st.checkbox(t, key=f"{key}{cid}_f{k}") for k, t in enumerate(FINAL_CHECK)]
    score = round(0.7 * pct + 30 * sum(chk) / len(chk))
    label = "Good" if score >= 80 else "Fair" if score >= 50 else "At risk"
    m[3].metric("Security score", label)
    st.markdown("**Updates**")
    for e in db.events(cid):
        st.write(f"{e['at'][:16].replace('T', ' ')}: {e['note']}")
    done = db.done(cid)
    report = (f"CyberShield recovery report {cid}\nAttack: {c['attack']}\nFiled: {c['created']}\nStatus: {c['status']}\n"
              f"Severity: {c['severity']}\nRecovery: {pct}% ({n} of {total} steps)\nSecurity score: {label}\n\n" +
              "\n".join(("[x] " if i in done else "[ ] ") + BY_ID[i].text.replace("the platform", plat) for i in plan))
    st.download_button("Download recovery report", report, file_name=f"{cid}_report.txt", key=f"{key}{cid}_dl")


def report_page(u):
    st.header("Report a cyber incident")
    attack = st.selectbox("What happened?", list(ATTACKS))
    code, _, validated = ATTACKS[attack]
    also = st.multiselect("Was anything else affected?", [k for k in INCIDENTS if k != code], format_func=INCIDENTS.get)
    incs = [code] + also
    if not validated:
        st.info("This attack type uses the closest guidance we have. It was not part of the evaluation.")
    obs = study.ask(incs, "r_")
    when = st.date_input("When did it happen?")
    desc = st.text_area("Describe what happened")
    contact = st.text_input("Contact details (phone or email)")
    sev0 = db.suggest_severity(obs, incs)
    sev = st.selectbox("Severity", LEVELS, index=LEVELS.index(sev0), help="Suggested from your answers. An administrator may change it.")
    up = st.file_uploader("Evidence (screenshot or file)")
    if st.button("Submit and get my recovery plan"):
        if not desc.strip():
            st.error("Add a short description so an investigator can follow up.")
            return
        plan = [a.id for a, _ in ENGINES[SYSTEM](incs, obs)]
        cid = db.create_complaint(u["id"], attack, incs, SYSTEM, f"[{when}] {desc}", contact, "", obs, plan, sev)
        if up:
            Path("data/evidence").mkdir(parents=True, exist_ok=True)
            path = Path("data/evidence") / f"{cid}_{Path(up.name).name}"
            path.write_bytes(up.getvalue())
            with db.conn() as c:
                c.execute("update complaints set evidence=? where cid=?", (str(path), cid))
        st.session_state["open"] = cid
        st.success(f"Complaint ID {cid}. Your plan is below and saved under My complaints.")
    if st.session_state.get("open"):
        recovery(db.get(st.session_state["open"]), "new_")


def my_page(u):
    st.header("My complaints")
    mine = db.complaints(user_id=u["id"])
    if not mine:
        st.info("You haven’t reported anything yet. Use Report an incident to get a recovery plan.")
        return
    pick = st.selectbox("Complaint", [c["cid"] for c in mine],
                        format_func=lambda i: next(f"{c['cid']}: {c['attack']} ({c['status']})" for c in mine if c["cid"] == i))
    recovery(db.get(pick), "my_")


def awareness_page():
    st.header("Stay safe")
    alerts = db.alerts()
    st.subheader("Scam alerts")
    for a in alerts:
        st.warning(f"**{a['title']}** ({a['at'][:10]}). {a['body']}")
    if not alerts:
        st.write("No alerts have been posted yet.")
    for tab, (name, tips) in zip(st.tabs(list(TIPS)), TIPS.items()):
        with tab:
            for t in tips:
                st.write("- " + t)


def admin_complaints():
    st.header("All complaints")
    c1, c2 = st.columns(2)
    q = c1.text_input("Search by ID, attack, description or investigator")
    status = c2.selectbox("Status", [""] + STATUSES, format_func=lambda s: s or "Any")
    rows = db.complaints(q=q, status=status)
    rank = {"High": 0, "Medium": 1, "Low": 2}
    rows.sort(key=lambda c: (rank[c["severity"]], c["created"]))
    st.dataframe(pd.DataFrame(rows, columns=["cid", "attack", "severity", "status", "investigator", "created"]))
    if not rows:
        return
    cid = st.selectbox("Open complaint", [c["cid"] for c in rows])
    c = db.get(cid)
    st.write(f"**{c['attack']}**. Contact: {c['contact'] or 'none'}")
    st.write(c["description"])
    st.write("Reported facts:", json.loads(c["facts"]))
    if c["evidence"] and Path(c["evidence"]).exists():
        st.download_button("Download evidence", Path(c["evidence"]).read_bytes(), file_name=Path(c["evidence"]).name)
    n, total = pct_done(c)
    st.write(f"User recovery progress: {n} of {total} steps")
    with st.form("upd"):
        s = st.selectbox("Status", STATUSES, index=STATUSES.index(c["status"]))
        v = st.selectbox("Severity", LEVELS, index=LEVELS.index(c["severity"]))
        who = st.text_input("Investigator", c["investigator"])
        note = st.text_input("Note to the user (optional)")
        if st.form_submit_button("Save update"):
            db.update(cid, s, v, who, note)
            st.success("Updated. The user sees this in their timeline.")


def analytics_page():
    st.header("Analytics")
    df = db.overview()
    if df.empty:
        st.info("No complaints yet.")
        return
    a, b, c = st.columns(3)
    a.metric("Complaints", len(df)); b.metric("Resolved or closed", int(df.status.isin(["Resolved", "Closed"]).sum()))
    c.metric("Average recovery", f"{df.recovery_pct.mean():.0f}%")
    for col in ["attack", "severity", "status"]:
        st.subheader(f"By {col}")
        st.bar_chart(df[col].value_counts())
    st.download_button("Export report (CSV)", df.to_csv(index=False), file_name="cybershield_report.csv")


def alerts_page():
    st.header("Post a scam alert")
    with st.form("alert"):
        t, body = st.text_input("Title"), st.text_area("What people should know")
        if st.form_submit_button("Publish") and t and body:
            db.add_alert(t, body)
            st.success("Published. Users see it under Stay safe.")


def main():
    u = st.session_state.get("user")
    if not u:
        style.hero("CyberShield", "Report a cyber incident and get a recovery plan that fits what happened to you.")
        t1, t2 = st.tabs(["Log in", "Create account"])
        with t1:
            name, pw = st.text_input("Username", key="ln"), st.text_input("Password", type="password", key="lp")
            if st.button("Log in"):
                u = db.login(name, pw)
                if u:
                    st.session_state["user"] = u
                    st.rerun()
                st.error("Wrong username or password.")
        with t2:
            name, pw = st.text_input("Choose a username", key="rn"), st.text_input("Choose a password (6+ characters)", type="password", key="rp")
            if st.button("Create account"):
                try:
                    db.register(name, pw)
                    st.success("Account created. You can log in now.")
                except ValueError as e:
                    st.error(str(e))
        return
    admin = u["role"] == "admin"
    pages = (["All complaints", "Analytics", "Scam alerts", "Research", "Stay safe"] if admin
             else ["Report an incident", "My complaints", "Stay safe"])
    with st.sidebar:
        style.brand()
        st.write(f"Signed in as **{u['username']}**")
        page = st.radio("Go to", pages)
        if st.button("Log out"):
            st.session_state.clear()
            st.rerun()
    {"Report an incident": lambda: report_page(u), "My complaints": lambda: my_page(u), "Stay safe": awareness_page,
     "All complaints": admin_complaints, "Analytics": analytics_page, "Scam alerts": alerts_page,
     "Research": study.page}[page]()


main()

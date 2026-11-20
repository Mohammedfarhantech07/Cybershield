"""CyberShield action library. Have a bank fraud officer and a security responder review it before real use."""
from dataclasses import dataclass

INCIDENTS = {"ph": "Phishing", "upi": "UPI / online-payment fraud", "hk": "Hacked account",
             "rw": "Ransomware / malware", "id": "Identity theft"}
FACTS = {"money": "Money was debited", "otp": "Shared an OTP or UPI PIN, or approved a collect request",
         "app": "Installed an unknown app or attachment", "cred": "Typed a password or card details into a fake page",
         "reuse": "Uses that password on other accounts", "login": "Can still sign in to the account",
         "mfa": "Two-factor login was already on", "work": "Work or office device",
         "paid": "Paid (or is considering paying) the ransom", "backup": "Has a clean offline backup",
         "docs": "ID documents (Aadhaar, PAN) were exposed"}
INCIDENT_FACTS = {"ph": ["cred", "reuse", "money", "app"], "upi": ["money", "otp", "app"],
                  "hk": ["login", "mfa", "reuse", "money"], "rw": ["work", "paid", "backup"],
                  "id": ["docs", "money", "cred"]}
# Population priors: how likely each fact is to be true. Replace with real data when you have it.
PRIOR = {"money": .5, "otp": .4, "app": .3, "cred": .5, "reuse": .6, "login": .5, "mfa": .4,
         "work": .3, "paid": .2, "backup": .35, "docs": .4}


@dataclass(frozen=True)
class Action:
    id: str
    text: str
    why: str
    urg: int            # 1-5; 5 = act now
    inc: frozenset      # incidents where the action is relevant
    core: frozenset     # incidents where it sits on the generic fixed checklist
    rule: str           # single-fact rule used by System B ("fact" or "!fact"; "" = always)
    need: object        # (facts, incident_set) -> bool: is the action essential? (answer key)
    after: tuple = ()   # actions that should come first


def _a(id, text, why, urg, inc, core, rule, need, after=()):
    return Action(id, text, why, urg, frozenset(inc.split()), frozenset(core.split()), rule, need, after)


T = lambda c, I: True
ACTIONS = [
    _a("stop", "Stop engaging: don’t reply, click or call back. Screenshot the message.",
       "Stops further manipulation and keeps evidence.", 3, "ph", "ph", "", T),
    _a("h1930", "Call 1930 right away; a fast report can help freeze the funds.",
       "Money moves on quickly; early reports give the best chance of stopping it.", 5,
       "ph upi hk id rw", "upi", "money", lambda c, I: c["money"]),
    _a("bank", "Call your bank now (zero-liability cover depends on reporting within 3 working days) to block the card, account or UPI ID and get a reference number.",
       "RBI’s limited-liability rules reward prompt reporting.", 5, "ph upi hk id", "ph upi id", "money",
       lambda c, I: c["money"] or c["otp"]),
    _a("evidence", "Save screenshots, transaction IDs and the scammer’s number or UPI ID. Decline pending collect requests.",
       "Banks and police need these details.", 3, "upi id", "upi", "", T),
    _a("pin", "Change your UPI PIN and re-register the UPI app.", "A shared PIN or OTP can be used again.", 4,
       "upi", "upi", "otp", lambda c, I: c["otp"] or c["app"], ("bank",)),
    _a("pw_fake", "Change the password of the account you typed into the fake page and sign out other sessions.",
       "Whoever has that password can sign in now.", 5, "ph", "ph", "cred", lambda c, I: c["cred"]),
    _a("pw_reuse", "Change the same password on every other account that reuses it.",
       "Attackers try stolen passwords on other sites.", 4, "ph hk", "", "reuse",
       lambda c, I: c["reuse"] and (c["cred"] or "hk" in I), ("pw_fake", "login_pw", "recover")),
    _a("rm_app", "Remove the unknown app or attachment (screen-sharing, APK) and run a malware scan.",
       "It may still be watching your phone or computer.", 4, "ph upi hk", "", "app", lambda c, I: c["app"]),
    _a("login_pw", "Change the password from a trusted device and sign out of all sessions.",
       "Cuts off the attacker while you still have access.", 5, "hk", "hk", "login", lambda c, I: c["login"]),
    _a("recover", "Use the platform’s official account-recovery flow and report the hack.",
       "You can’t secure an account you can’t reach.", 5, "hk", "hk", "!login", lambda c, I: not c["login"]),
    _a("hk_dev", "Remove unknown devices, apps and changed recovery email or phone numbers.",
       "Leftover recovery options let the attacker back in.", 4, "hk", "hk", "", T),
    _a("mfa", "Turn on two-factor login with an authenticator app.", "A stolen password alone then isn’t enough.", 4,
       "hk id rw", "hk id rw", "!mfa", lambda c, I: not c["mfa"], ("login_pw", "recover")),
    _a("warn", "Warn your contacts about messages sent from your account.", "Stops the scam spreading.", 2, "hk", "", "", T),
    _a("disconnect", "Disconnect the device from Wi-Fi and network cables right away.", "Stops encryption spreading.", 5,
       "rw", "rw", "", T),
    _a("it", "Tell your IT or security team; organisations also report to CERT-In.", "Work systems may be exposed too.", 5,
       "rw", "rw", "work", lambda c, I: c["work"]),
    _a("noransom", "Don’t pay the ransom. Check nomoreransom.org for a free decryptor.", "Payment doesn’t guarantee recovery.", 4,
       "rw", "rw", "", T),
    _a("paid", "If you already paid, tell your bank and report on cybercrime.gov.in.", "Payment trails help recovery.", 3,
       "rw", "", "paid", lambda c, I: c["paid"]),
    _a("restore", "Restore from a clean offline backup once the device is cleaned.", "Backups are the safe way back.", 4,
       "rw", "rw", "backup", lambda c, I: c["backup"], ("disconnect",)),
    _a("keep", "Keep the encrypted files and ransom note; don’t wipe the disk yet.", "A decryptor may appear later.", 3,
       "rw", "", "!backup", lambda c, I: not c["backup"]),
    _a("rw_pw", "Change passwords from a clean device.", "Malware may have captured the old ones.", 4,
       "rw", "rw", "", T, ("disconnect",)),
    _a("aadhaar", "Lock your Aadhaar biometrics and review authentication history on the UIDAI site or app.",
       "Blocks misuse of your biometrics.", 4, "id", "", "docs", lambda c, I: c["docs"]),
    _a("sim", "Check mobile connections issued in your name on Sanchar Saathi and report unknown ones.",
       "Fraudsters open SIMs with stolen documents.", 4, "id", "", "docs", lambda c, I: c["docs"]),
    _a("credit", "Pull your credit reports (CIBIL, Experian, Equifax, CRIF) and dispute loans you don’t recognise.",
       "Shows whether credit was taken in your name.", 4, "id", "id", "", T),
    _a("id_pw", "Change passwords for email, banking and government portals.", "Exposed credentials get reused.", 4,
       "id", "id", "cred", lambda c, I: c["cred"]),
    _a("monitor", "Watch statements and credit reports for the next 6 to 12 months.", "Misuse can surface late.", 2,
       "id", "", "", T),
    _a("report", "File a complaint on cybercrime.gov.in.", "Creates an official record police can track.", 3,
       "ph upi hk rw id", "ph upi hk rw id", "", T),
]
BY_ID = {a.id: a for a in ACTIONS}


def full(c):
    return {f: bool(c.get(f, False)) for f in FACTS}


def essential(I, c):
    """Answer key: ids of actions that are essential for incident set I given true facts c."""
    c, I = full(c), set(I)
    return {a.id for a in ACTIONS if a.inc & I and a.need(c, I)}

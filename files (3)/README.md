# CyberShield

Cyber incident reporting, personalised recovery guidance, and a built-in evaluation of three guidance methods.

## Run
    python server.py
Opens http://127.0.0.1:8000 (local only). First admin login: `admin` / `admin123`, or set `CYBERSHIELD_ADMIN_PW` before the very first run.
Keep `web/index.html` inside a folder named `web` next to `server.py`. Needs only Python 3.10+ and `pip install -r requirements.txt` (pandas, matplotlib).

## Roles
- **Member:** register, report one of 16 attack types (optional evidence upload), get a recovery plan, tick steps, follow status updates, download a report, read tips and alerts.
- **Admin:** search and sort complaints (High first), change status, severity and investigator with a note the user sees, post scam alerts, analytics, CSV export, Research pages.
- **Research (admin):** Study mode runs the human experiment (3 fictional cases, rotating A/B/C, timed, 1-7 ratings) into `data/study_log.csv`. `python experiment.py` runs the simulation.

## Files
`server.py` web server and API · `web/index.html` the interface · `library.py` actions and answer key (have experts review) · `engines.py` systems A, B, C · `experiment.py` simulation · `db.py` SQLite · `attacks.py` attack types and tips
Older Streamlit interface (optional): `app.py`, `style.py`, `study.py`.

## Limits
Guidance is for India (1930, cybercrime.gov.in, RBI 3-working-day rule). Credit card fraud, OTP scam, data breach, password leak and Wi-Fi attack reuse the nearest evaluated guidance. Simulation results are not evidence about people; use Study mode for that. Not a substitute for your bank or the police.

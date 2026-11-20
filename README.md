# CyberShield

Cyber incident reporting, personalised recovery guidance and a built-in evaluation of three guidance methods.

## Run
    pip install -r requirements.txt
    streamlit run app.py
First admin login: `admin` / `admin123` (or set `CYBERSHIELD_ADMIN_PW` before the first run). Change it. Data lives in `data/`.

## Roles
- **User:** register, report one of 16 attack types (with evidence upload), get a recovery plan, tick steps, see status updates, download a report, read safety tips and scam alerts.
- **Admin:** search and sort complaints (High first), change status, severity and investigator (with a note the user sees), post scam alerts, view analytics, export CSV, open the Research pages.
- **Research (admin):** Study mode runs the human experiment (3 fictional cases, rotating A/B/C, timed, with 1-7 ratings) and logs to `data/study_log.csv`. `python experiment.py` runs the simulation.

## Files
`library.py` actions and answer key (have experts review) · `engines.py` systems A, B, C · `experiment.py` simulation · `db.py` SQLite · `attacks.py` attack types, tips · `study.py` research pages · `app.py` UI

## Limits
Guidance is for India (1930, cybercrime.gov.in, RBI 3-working-day rule). Credit card fraud, OTP scam, data breach, password leak and Wi-Fi attack reuse the nearest evaluated guidance. Simulation results are not evidence about people; use Study mode for that. Not a substitute for your bank or the police.

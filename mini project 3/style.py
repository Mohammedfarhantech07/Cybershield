"""Look and feel: theme, animations, hero header, badges. Change the colours below to restyle the whole app."""
from pathlib import Path
import streamlit as st

ACCENT, ACCENT2, BG = "#22D3EE", "#6366F1", "#0A1220"
SEV = {"High": "#F87171", "Medium": "#FBBF24", "Low": "#4ADE80"}
THEME = f'[theme]\nbase = "dark"\nprimaryColor = "{ACCENT}"\nbackgroundColor = "{BG}"\nsecondaryBackgroundColor = "#111C30"\ntextColor = "#E6EEF8"\n'

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&display=swap');
.stApp{background:radial-gradient(1100px 560px at 85% -10%,rgba(34,211,238,.15),transparent 60%),radial-gradient(900px 520px at -10% 110%,rgba(99,102,241,.17),transparent 55%),@BG}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.02em}
.block-container{animation:rise .6s ease both}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes flow{to{background-position:-200% 0}}
@keyframes float{50%{transform:translateY(-8px)}}
[data-testid="stSidebar"]{background:rgba(17,28,48,.88);backdrop-filter:blur(10px);border-right:1px solid rgba(34,211,238,.16)}
[data-testid="stMetric"]{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.09);border-radius:14px;padding:14px 16px;transition:transform .25s,border-color .25s,box-shadow .25s}
[data-testid="stMetric"]:hover{transform:translateY(-3px);border-color:rgba(34,211,238,.55);box-shadow:0 8px 24px rgba(34,211,238,.14)}
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"]>button{border-radius:12px;border:1px solid rgba(34,211,238,.45);background:linear-gradient(135deg,rgba(34,211,238,.18),rgba(99,102,241,.2));transition:transform .25s,box-shadow .25s}
.stButton>button:hover,.stDownloadButton>button:hover,[data-testid="stFormSubmitButton"]>button:hover{transform:translateY(-2px);box-shadow:0 0 0 1px rgba(34,211,238,.6),0 8px 22px rgba(34,211,238,.25)}
[data-testid="stProgress"] [role="progressbar"]>div{background:linear-gradient(90deg,@A,@B,@A);background-size:200% 100%;animation:flow 2.4s linear infinite}
[data-testid="stCheckbox"]{padding:6px 10px;border-radius:10px;transition:background .2s}
[data-testid="stCheckbox"]:hover{background:rgba(34,211,238,.08)}
[data-testid="stAlert"],[data-testid="stExpander"]{border-radius:12px}
input,textarea,[data-baseweb="select"]>div{border-radius:10px!important}
.hero{text-align:center;padding:36px 0 18px}
.shield{font-size:3.4rem;animation:float 3s ease-in-out infinite;filter:drop-shadow(0 0 18px rgba(34,211,238,.55))}
.grad{background:linear-gradient(90deg,@A,@B,@A);background-size:200% auto;-webkit-background-clip:text;background-clip:text;color:transparent;animation:flow 5s linear infinite}
.hero p{color:#9FB3C8;max-width:34rem;margin:0 auto}
.brand{font:700 1.25rem 'Space Grotesk',sans-serif;margin-bottom:6px}
.pill{display:inline-block;padding:2px 10px;margin-left:6px;border:1px solid;border-radius:999px;font-size:.78rem;font-weight:600}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>""".replace("@A", ACCENT).replace("@B", ACCENT2).replace("@BG", BG)


def inject():
    cfg = Path(".streamlit/config.toml")
    if not cfg.exists():   # saves the dark theme once; it applies the next time the app starts
        cfg.parent.mkdir(exist_ok=True)
        cfg.write_text(THEME)
        st.toast("Theme saved. Stop the app (Ctrl+C) and start it again to apply the full dark theme.")
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title, sub):
    st.markdown(f'<div class="hero"><div class="shield">🛡️</div><h1 class="grad">{title}</h1><p>{sub}</p></div>', unsafe_allow_html=True)


def brand():
    st.markdown('<div class="brand">🛡️ CyberShield</div>', unsafe_allow_html=True)


def badge(text, color):
    return f'<span class="pill" style="color:{color};border-color:{color}66;background:{color}1A">{text}</span>'

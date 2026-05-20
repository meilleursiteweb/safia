"""
Safia Rugs — Agent SEO IA
Plateforme professionnelle d'intelligence concurrentielle & création de contenu
"""

import streamlit as st
import sys, os, json, pandas as pd, base64, io
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

# ── Streamlit Cloud — injecte les secrets dans os.environ ─────────────────────
# Sur Streamlit Cloud il n'y a pas de .env ; on lit st.secrets à la place.
# Localement st.secrets est vide → ce bloc ne fait rien.
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
    # google_credentials.json stocké comme chaîne JSON dans le secret GOOGLE_CREDS_JSON
    if "GOOGLE_CREDS_JSON" in st.secrets:
        _cp = os.path.join(os.path.dirname(__file__), "google_credentials.json")
        if not os.path.exists(_cp):
            with open(_cp, "w", encoding="utf-8") as _f:
                _f.write(st.secrets["GOOGLE_CREDS_JSON"])
except Exception:
    pass

load_dotenv(override=True)  # Relit .env à chaque rerun → permet le changement de mot de passe

def _update_env_password(new_pass: str) -> bool:
    """Met à jour DASHBOARD_PASSWORD dans le fichier .env."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(env_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(f"DASHBOARD_PASSWORD={new_pass}\n" if line.startswith("DASHBOARD_PASSWORD=") else line)
        return True
    except Exception:
        return False

def _logo_b64() -> str:
    """Charge le logo, supprime le fond blanc, retourne PNG blanc/transparent en base64."""
    path = os.path.join(os.path.dirname(__file__), "safia.png")
    img = Image.open(path).convert("RGBA")
    pixels = img.getdata()
    result = []
    for r, g, b, a in pixels:
        if r > 200 and g > 200 and b > 200:
            result.append((255, 255, 255, 0))
        else:
            brightness = 255 - int((r + g + b) / 3)
            result.append((255, 255, 255, brightness))
    img.putdata(result)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def _logo_dark_b64() -> str:
    """Charge le logo, supprime le fond blanc, conserve les couleurs d'origine (pour fond clair)."""
    path = os.path.join(os.path.dirname(__file__), "safia.png")
    img = Image.open(path).convert("RGBA")
    pixels = img.getdata()
    result = []
    for r, g, b, a in pixels:
        if r > 210 and g > 210 and b > 210:
            result.append((r, g, b, 0))
        else:
            result.append((r, g, b, a))
    img.putdata(result)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

sys.path.insert(0, os.path.dirname(__file__))
from agent import (
    AgentSEOChat, run_analyse_complete, semaine_iso,
    suggerer_sujets_blog, generer_brief_seo, generer_article_complet,
    generer_calendrier_contenu, analyser_mon_site,
    lire_tous_concurrents, ajouter_concurrent, desactiver_concurrent, reactiver_concurrent,
    verifier_analyse_due,
    SAFIA_CONTEXT,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Safia Rugs — Agent SEO",
    page_icon="🏺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Credentials ───────────────────────────────────────────────────────────────
DASH_USER = os.getenv("DASHBOARD_USER", "safia")
DASH_PASS = os.getenv("DASHBOARD_PASSWORD", "safia2026")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


# ══════════════════════════════════════════════════════════════════════════════
# PAGE LOGIN
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.authenticated:

    # ── CSS page login ──────────────────────────────────────────────────────────
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Cormorant+Garamond:wght@400;500;600&display=swap');

#MainMenu, header, footer { visibility: hidden; }
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
.stDeployButton { display: none !important; }

.stApp {
    background: linear-gradient(145deg, #f5ede8 0%, #edddd6 40%, #e4cec5 100%);
    min-height: 100vh;
}

.main .block-container {
    padding-top: 7vh !important;
    padding-bottom: 4vh !important;
    max-width: 100% !important;
}

/* ─── Card effet sur la colonne centrale ─── */
/* st.columns() génère [data-testid="column"] — le wrapper HTML div ne fonctionne
   pas avec les éléments Streamlit, on cible donc la colonne directement */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {
    background: white !important;
    border-radius: 22px !important;
    padding: 40px 36px 32px !important;
    box-shadow:
        0 24px 64px rgba(180,110,90,0.16),
        0 4px 18px rgba(0,0,0,0.07) !important;
    border-top: 4px solid #c97b6e !important;
    animation: cardIn 0.35s ease !important;
}
@keyframes cardIn {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* Labels */
div[data-testid="stTextInput"] label {
    color: #8a6058 !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    font-family: 'DM Sans', sans-serif !important;
    margin-bottom: 4px !important;
    display: block !important;
}

/* Inputs */
div[data-testid="stTextInput"] input {
    background: #faf6f4 !important;
    border: 1.5px solid #e8d4cc !important;
    border-radius: 10px !important;
    color: #2a1510 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
    transition: border-color 0.22s, box-shadow 0.22s !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #c97b6e !important;
    box-shadow: 0 0 0 3px rgba(201,123,110,0.13) !important;
    background: white !important;
    outline: none !important;
}
div[data-testid="stTextInput"] input::placeholder {
    color: #c4a89e !important;
}

/* Bouton */
.stButton > button {
    background: linear-gradient(135deg, #c97b6e 0%, #b5604f 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    height: 52px !important;
    box-shadow: 0 4px 20px rgba(201,123,110,0.35) !important;
    transition: all 0.22s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 32px rgba(201,123,110,0.48) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* Alerte erreur */
.stAlert {
    border-radius: 10px !important;
    font-size: 13px !important;
}
</style>
""", unsafe_allow_html=True)

    # ── Layout centré avec colonnes ─────────────────────────────────────────────
    _, col_c, _ = st.columns([1, 1.2, 1])
    with col_c:
        # Logo centré — st.image() ne supporte pas le centrage,
        # on utilise du HTML avec base64 pour un rendu fiable
        logo_path = os.path.join(os.path.dirname(__file__), "safia.png")
        with open(logo_path, "rb") as _f:
            _logo_raw = base64.b64encode(_f.read()).decode()
        st.markdown(f"""
<div style="display:flex; justify-content:center; margin-bottom:2px">
  <img src="data:image/png;base64,{_logo_raw}"
       style="width:190px; height:auto; border-radius:6px">
</div>
""", unsafe_allow_html=True)

        st.markdown("""
<div style="margin:6px 0 26px">
  <div style="height:1px; background:linear-gradient(90deg,transparent,#e8d4cc,transparent);
              margin-bottom:14px"></div>
  <div style="font-size:10px; color:#b09088; letter-spacing:3px; text-transform:uppercase;
              font-family:'DM Sans',sans-serif; text-align:center">
    Agent SEO IA &nbsp;·&nbsp; Plateforme Privée
  </div>
</div>
""", unsafe_allow_html=True)

        username = st.text_input("Identifiant", placeholder="Votre identifiant", key="l_user")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        password = st.text_input("Mot de passe", type="password", placeholder="••••••••••", key="l_pass")
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        if st.button("Accéder au dashboard", use_container_width=True):
            if username == DASH_USER and password == DASH_PASS:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Identifiants incorrects — vérifiez votre identifiant et mot de passe.")

        st.markdown("""
<div style="text-align:center; margin-top:22px; font-size:11px; color:#c4a89e;
            font-family:'DM Sans',sans-serif; letter-spacing:0.5px">
  🔒 Accès réservé à l'équipe Safia Rugs
</div>
""", unsafe_allow_html=True)

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# CSS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,700;1,400&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, .stDeployButton { visibility: hidden; }
.stApp { background: #f4f6f9; }
.main .block-container { padding-top: 18px !important; padding-bottom: 24px !important; }

/* ════════════════════════ PAGE HEADER ════════════════════════ */
.page-header {
    background: linear-gradient(135deg, #1e0d09 0%, #2d1610 55%, #3a1d14 100%);
    color: white;
    padding: 18px 26px;
    border-radius: 16px;
    margin-bottom: 14px;
    border-bottom: 3px solid #c97b6e;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 24px rgba(30,13,9,0.22);
}
.page-header-brand {
    display: flex;
    align-items: center;
    gap: 16px;
}
.page-header-text h1 {
    font-family: 'Playfair Display', serif;
    font-size: 19px;
    margin: 0 0 3px 0;
    font-weight: 700;
    letter-spacing: 0.2px;
}
.page-header-text p {
    opacity: 0.45;
    font-size: 11px;
    margin: 0;
    letter-spacing: 0.3px;
}
.page-header-right {
    display: flex;
    align-items: center;
    gap: 14px;
}
.week-pill {
    background: rgba(201,123,110,0.18);
    border: 1px solid rgba(201,123,110,0.4);
    color: #e8a090;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    white-space: nowrap;
}
.greeting-block {
    text-align: right;
}
.greeting-block .greeting-name {
    font-size: 13px;
    font-weight: 600;
    color: rgba(255,255,255,0.88);
}
.greeting-block .greeting-date {
    font-size: 10px;
    color: rgba(255,255,255,0.38);
    letter-spacing: 0.3px;
    margin-top: 2px;
}

/* ════════════════════════ STATS BAR ════════════════════════ */
.stats-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 18px;
    flex-wrap: wrap;
}
.stat-chip {
    background: white;
    border: 1px solid #eaecf0;
    border-top: 3px solid #ddd8d0;
    border-radius: 12px;
    padding: 16px 22px 14px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    flex: 1;
    min-width: 130px;
    transition: box-shadow 0.18s, transform 0.18s;
}
.stat-chip:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}
.stat-chip-val {
    font-size: 26px;
    font-weight: 700;
    color: #0a0f1e;
    line-height: 1;
    margin-bottom: 6px;
}
.stat-chip-label {
    font-size: 10px;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ════════════════════════ KPI CARDS ════════════════════════ */
.kpi-card {
    background: white;
    border: 1px solid #eaecf0;
    border-radius: 14px;
    padding: 20px 14px;
    text-align: center;
    box-shadow: 0 1px 8px rgba(0,0,0,0.04);
    transition: transform 0.18s, box-shadow 0.18s;
    border-top: 3px solid #ddd8d0;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.09); }
.kpi-card.gold  { border-top-color: #C9A96E; }
.kpi-card.red   { border-top-color: #e11d48; }
.kpi-card.green { border-top-color: #16a34a; }
.kpi-card.blue  { border-top-color: #2563eb; }
.kpi-val  { font-size: 30px; font-weight: 700; color: #0a0f1e; line-height: 1.1; }
.kpi-lab  { font-size: 10px; color: #9ca3af; margin-top: 7px; text-transform: uppercase; letter-spacing: 1px; }
.kpi-gold  { color: #b8872a !important; }
.kpi-red   { color: #e11d48 !important; }
.kpi-green { color: #16a34a !important; }

/* ════════════════════════ SECTION TITLES ════════════════════════ */
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 16px;
    color: #1e0d09;
    margin: 18px 0 12px 0;
    padding-bottom: 7px;
    border-bottom: 2px solid #c97b6e;
    display: inline-block;
    letter-spacing: 0.2px;
    font-weight: 700;
}

/* ════════════════════════ PANEL CARDS ════════════════════════ */
.panel {
    background: white;
    border-radius: 14px;
    padding: 22px 20px;
    border: 1px solid #eaecf0;
    box-shadow: 0 1px 8px rgba(0,0,0,0.04);
    margin-bottom: 14px;
}

/* ════════════════════════ BADGES ════════════════════════ */
.badge {
    padding: 3px 10px; border-radius: 20px; font-size: 10px;
    font-weight: 700; display: inline-block; letter-spacing: 0.5px; text-transform: uppercase;
}
.badge-haute    { background: #fee2e2; color: #dc2626; }
.badge-moyenne  { background: #fef3c7; color: #b45309; }
.badge-faible   { background: #f3f4f6; color: #6b7280; }
.badge-critique { background: #ede9fe; color: #7c3aed; }
.badge-ok       { background: #dcfce7; color: #15803d; }
.badge-actif    { background: #dcfce7; color: #15803d; }
.badge-inactif  { background: #f3f4f6; color: #9ca3af; }

/* ════════════════════════ QUICK WINS ════════════════════════ */
.qw-card {
    background: white;
    border-left: 4px solid #c97b6e;
    padding: 12px 16px;
    border-radius: 0 10px 10px 0;
    margin: 6px 0;
    box-shadow: 0 1px 6px rgba(0,0,0,0.05);
    transition: box-shadow 0.18s;
}
.qw-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.09); }
.qw-card.fort  { border-left-color: #dc2626; }
.qw-card.moyen { border-left-color: #d97706; }

/* ════════════════════════ BLOG CARDS ════════════════════════ */
.blog-card {
    background: white;
    border: 1px solid #eaecf0;
    border-radius: 12px;
    padding: 16px 18px;
    margin: 8px 0;
    border-top: 3px solid #c97b6e;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s, transform 0.2s;
}
.blog-card:hover { box-shadow: 0 6px 20px rgba(0,0,0,0.09); transform: translateY(-1px); }

/* ════════════════════════ CHAT ════════════════════════ */
.chat-user {
    background: linear-gradient(135deg, #0a0f1e 0%, #152847 100%);
    color: white; padding: 12px 18px; border-radius: 18px 18px 4px 18px;
    margin: 8px 0 8px 80px; font-size: 14px; line-height: 1.6;
    box-shadow: 0 3px 12px rgba(10,15,30,0.22);
}
.chat-agent {
    background: white; border-left: 3px solid #c97b6e;
    padding: 14px 18px; border-radius: 4px 18px 18px 18px;
    margin: 8px 80px 8px 0; font-size: 14px; line-height: 1.75;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}

/* ════════════════════════ ALERTS ════════════════════════ */
.alert-critique { background:#fff1f2; border:1px solid #fda4af; border-left:4px solid #e11d48; border-radius:10px; padding:14px 18px; }
.alert-info     { background:#eff6ff; border:1px solid #bfdbfe; border-left:4px solid #3b82f6; border-radius:10px; padding:14px 18px; }
.alert-success  { background:#f0fdf4; border:1px solid #bbf7d0; border-left:4px solid #16a34a; border-radius:10px; padding:14px 18px; }
.alert-warning  { background:#fffbeb; border:1px solid #fde68a; border-left:4px solid #d97706; border-radius:10px; padding:14px 18px; }

/* ════════════════════════ SIDEBAR ════════════════════════ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #cda49f 0%, #c49490 55%, #bf8e8a 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.22) !important;
}
[data-testid="stSidebar"] * { color: #2a1410 !important; }
[data-testid="stSidebar"] hr { border-color: rgba(42,20,16,0.14) !important; }
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.3) !important;
    border: 1px solid rgba(255,255,255,0.45) !important;
    color: #2a1410 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    text-align: left !important;
    transition: all 0.18s !important;
    padding: 9px 13px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.55) !important;
    border-color: rgba(255,255,255,0.75) !important;
    color: #1a0a08 !important;
    transform: translateX(3px) !important;
}
[data-testid="stSidebar"] .stButton > button[data-testid*="logout"] {
    background: rgba(180,30,30,0.1) !important;
    border-color: rgba(180,30,30,0.22) !important;
    color: #7f1d1d !important;
}
[data-testid="stSidebar"] .stButton > button[data-testid*="logout"]:hover {
    background: rgba(180,30,30,0.2) !important;
    color: #991b1b !important;
    transform: translateX(0) !important;
}

/* ════════════════════════ BUTTONS ════════════════════════ */
.stButton > button {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    transition: all 0.18s !important;
}

/* ════════════════════════ TABS ════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 2px solid #eaecf0;
    background: transparent;
    padding-bottom: 0;
    margin-bottom: 6px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 10px 20px !important;
    border-radius: 8px 8px 0 0 !important;
    color: #6b7280 !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
    transition: all 0.18s !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #1e0d09 !important;
    background: rgba(201,123,110,0.05) !important;
}
.stTabs [aria-selected="true"] {
    color: #1e0d09 !important;
    background: transparent !important;
    border-bottom: 2px solid #c97b6e !important;
    font-weight: 600 !important;
}

/* ════════════════════════ DATAFRAME ════════════════════════ */
.stDataFrame { border-radius: 12px !important; overflow: hidden; }
.stDataFrame thead th {
    background: #f8f9fb !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    color: #374151 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
.streamlit-expanderHeader {
    border-radius: 9px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    background: white !important;
    border: 1px solid #eaecf0 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────────────────────────────────────
defaults = {
    "agent": AgentSEOChat(), "messages": [], "rapport": None, "lancer": False,
    "sujets_blog": [], "brief_actuel": None, "article_actuel": None,
    "mon_site": None, "lancer_mon_site": False,
    "calendrier": [], "lancer_calendrier": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Analyse automatique toutes les 2 semaines ──────────────────────────────────
if "auto_analyse_checked" not in st.session_state:
    st.session_state.auto_analyse_checked = True
    try:
        _due, _due_msg = verifier_analyse_due()
        if _due and not st.session_state.lancer:
            st.session_state.lancer = True
            st.session_state.auto_analyse_msg = _due_msg
    except Exception:
        pass  # Silencieux si Google Sheets inaccessible


# ── Sidebar ────────────────────────────────────────────────────────────────────
_logo      = _logo_b64()        # version blanche — pour fond sombre (page header)
_logo_dark = _logo_dark_b64()   # couleurs d'origine — pour la sidebar rose
with st.sidebar:
    st.markdown(f"""
<div style="padding:18px 8px 14px; text-align:center;
            border-bottom:1px solid rgba(42,20,16,0.12); margin-bottom:14px">
  <img src="data:image/png;base64,{_logo_dark}"
       style="width:120px; opacity:0.92; margin-bottom:10px">
  <div style="font-size:9px; color:rgba(42,20,16,0.45); letter-spacing:3px; text-transform:uppercase">Agent SEO IA</div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div style="font-size:10px; color:rgba(42,20,16,0.48); letter-spacing:2px; margin-bottom:8px; padding-left:2px">ANALYSES</div>', unsafe_allow_html=True)
    if st.button("Analyser les concurrents", use_container_width=True):
        st.session_state.lancer = True
    if st.button("Analyser mon site", use_container_width=True):
        st.session_state.lancer_mon_site = True

    st.divider()
    st.markdown('<div style="font-size:10px; color:rgba(42,20,16,0.48); letter-spacing:2px; margin-bottom:8px; padding-left:2px">CONTENU BLOG</div>', unsafe_allow_html=True)
    if st.button("Suggestions d'articles", use_container_width=True):
        with st.spinner("Génération..."):
            analyses = st.session_state.rapport.get("toutes_analyses", []) if st.session_state.rapport else []
            st.session_state.sujets_blog = suggerer_sujets_blog(analyses, nb=10)
        st.rerun()
    if st.button("Calendrier 4 semaines", use_container_width=True):
        st.session_state.lancer_calendrier = True

    st.divider()
    st.markdown('<div style="font-size:10px; color:rgba(42,20,16,0.48); letter-spacing:2px; margin-bottom:8px; padding-left:2px">QUESTIONS RAPIDES</div>', unsafe_allow_html=True)
    questions_rapides = [
        "Quelles opportunités exploiter en priorité ?",
        "Quels mots-clés dominent nos concurrents ?",
        "Génère un article sur les tapis Azilal",
        "Comment améliorer mon SEO cette semaine ?",
    ]
    for q in questions_rapides:
        if st.button(q, use_container_width=True, key=f"sq_{hash(q)}"):
            st.session_state.messages.append({"role": "user", "content": q})
            rep = st.session_state.agent.chat(q)
            st.session_state.messages.append({"role": "assistant", "content": rep})
            st.rerun()

    st.divider()
    rapport = st.session_state.rapport
    if rapport:
        sm = rapport.get("score_menace", 5)
        col_m = "#c0392b" if sm >= 8 else "#b45309" if sm >= 6 else "#15803d"
        st.markdown(f"""
<div style="text-align:center; padding:10px 8px; background:rgba(255,255,255,0.25);
            border-radius:10px; border:1px solid rgba(255,255,255,0.4); margin-bottom:6px">
  <div style="font-size:9px; color:rgba(42,20,16,0.45); letter-spacing:2px">DERNIÈRE ANALYSE</div>
  <div style="font-size:22px; color:#7a4a1e; font-weight:700; margin:5px 0">{rapport.get('semaine_iso','—')}</div>
  <div style="font-size:12px; color:#2a1410">{rapport.get('nb_concurrents',0)} concurrents
    &nbsp;·&nbsp; <span style="color:{col_m}; font-weight:600">Menace {sm}/10</span></div>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="text-align:center; font-size:11px; color:rgba(42,20,16,0.4); padding:6px 0">Semaine {semaine_iso()}</div>', unsafe_allow_html=True)

    # ── User + Logout + Changement de mot de passe ──────────────────────────────
    st.divider()
    st.markdown(f"""
<div style="display:flex; align-items:center; gap:10px; padding:6px 4px; margin-bottom:10px">
  <div style="width:30px; height:30px; border-radius:50%;
              background:linear-gradient(135deg,#a0522d,#7a3a18);
              display:flex; align-items:center; justify-content:center;
              font-size:13px; color:#fff; font-weight:700; flex-shrink:0">
    {DASH_USER[0].upper()}
  </div>
  <div>
    <div style="font-size:13px; color:#1a0a08; font-weight:600">{DASH_USER.capitalize()}</div>
    <div style="font-size:10px; color:rgba(42,20,16,0.48)">Administrateur</div>
  </div>
</div>
""", unsafe_allow_html=True)

    with st.expander("Changer le mot de passe"):
        with st.form("pwd_form", clear_on_submit=True):
            old_pwd  = st.text_input("Mot de passe actuel", type="password", key="pwd_old")
            new_pwd  = st.text_input("Nouveau mot de passe", type="password", key="pwd_new")
            new_pwd2 = st.text_input("Confirmer", type="password", key="pwd_new2")
            if st.form_submit_button("Valider", use_container_width=True):
                if old_pwd != DASH_PASS:
                    st.error("Mot de passe actuel incorrect.")
                elif len(new_pwd) < 6:
                    st.error("6 caractères minimum.")
                elif new_pwd != new_pwd2:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    if _update_env_password(new_pwd):
                        st.success("Mot de passe mis à jour !")
                        st.rerun()
                    else:
                        st.error("Erreur lors de la mise à jour.")

    if st.button("Se déconnecter", use_container_width=True, key="logout_btn"):
        st.session_state.authenticated = False
        st.rerun()


# ── Header principal ───────────────────────────────────────────────────────────
_hour = datetime.now().hour
_greeting = "Bonjour" if 5 <= _hour < 12 else "Bon après-midi" if 12 <= _hour < 18 else "Bonsoir"
_date_fr = datetime.now().strftime("%A %d %B %Y").capitalize()

st.markdown(f"""
<div class="page-header">
  <div class="page-header-brand">
    <img src="data:image/png;base64,{_logo}"
         style="height:36px; opacity:0.9; flex-shrink:0">
    <div class="page-header-text">
      <h1>Safia Rugs — Agent SEO IA</h1>
      <p>"{SAFIA_CONTEXT['tagline']}" &nbsp;·&nbsp; Intelligence concurrentielle &nbsp;·&nbsp; Génération de contenu blog</p>
    </div>
  </div>
  <div class="page-header-right">
    <div class="greeting-block">
      <div class="greeting-name">{_greeting}, {DASH_USER.capitalize()} !</div>
      <div class="greeting-date">{_date_fr}</div>
    </div>
    <div class="week-pill">{semaine_iso()}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Stats bar (inspirée du design Mondays) ─────────────────────────────────────
_rp   = st.session_state.rapport
_nb_c = _rp.get("nb_concurrents", "—") if _rp else "—"
_nb_o = _rp.get("nb_opportunites", "—") if _rp else "—"
_sm   = _rp.get("score_menace", "—") if _rp else "—"
_sem  = _rp.get("semaine_iso", "—") if _rp else "—"
_sm_color = ("#e11d48" if isinstance(_sm, (int,float)) and _sm >= 8
             else "#d97706" if isinstance(_sm, (int,float)) and _sm >= 6
             else "#16a34a" if isinstance(_sm, (int,float))
             else "#9ca3af")

st.markdown(f"""
<div class="stats-bar">
  <div class="stat-chip" style="border-top-color:#2563eb">
    <div class="stat-chip-val">{_nb_c}</div>
    <div class="stat-chip-label">Concurrents surveillés</div>
  </div>
  <div class="stat-chip" style="border-top-color:#C9A96E">
    <div class="stat-chip-val">{_nb_o}</div>
    <div class="stat-chip-label">Opportunités détectées</div>
  </div>
  <div class="stat-chip" style="border-top-color:{_sm_color}">
    <div class="stat-chip-val" style="color:{_sm_color}">{_sm}{'&thinsp;/&thinsp;10' if _rp else ''}</div>
    <div class="stat-chip-label">Score de menace</div>
  </div>
  <div class="stat-chip" style="border-top-color:#6b7280">
    <div class="stat-chip-val" style="font-size:17px; font-weight:600">{_sem}</div>
    <div class="stat-chip-label">Dernière analyse</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Lancement analyses ─────────────────────────────────────────────────────────
if st.session_state.lancer:
    with st.status("🔍 Analyse concurrentielle en cours...", expanded=True) as status:
        try:
            st.write("📋 Lecture des concurrents depuis Google Sheets...")
            rapport = run_analyse_complete()
            st.session_state.rapport = rapport
            st.session_state.agent.definir_rapport(rapport)
            st.session_state.lancer = False
            status.update(label=f"✅ {rapport.get('nb_opportunites',0)} opportunités détectées !", state="complete")
            st.rerun()
        except Exception as e:
            st.session_state.lancer = False
            status.update(label=f"❌ {e}", state="error")

if st.session_state.lancer_mon_site:
    with st.status("🏠 Analyse de safia-rugs.com en cours...", expanded=True) as status:
        try:
            st.write("🌐 Scraping de safia-rugs.com...")
            analyses = st.session_state.rapport.get("toutes_analyses", []) if st.session_state.rapport else []
            mon_site = analyser_mon_site(analyses)
            st.session_state.mon_site = mon_site
            st.session_state.lancer_mon_site = False
            status.update(label=f"✅ Analyse terminée — Score SEO : {mon_site.get('score_seo_global',0)}/10", state="complete")
            st.rerun()
        except Exception as e:
            st.session_state.lancer_mon_site = False
            status.update(label=f"❌ {e}", state="error")

if st.session_state.lancer_calendrier:
    with st.spinner("📅 Génération du calendrier de contenu..."):
        analyses = st.session_state.rapport.get("toutes_analyses", []) if st.session_state.rapport else []
        st.session_state.calendrier = generer_calendrier_contenu(nb_semaines=4, analyses=analyses)
        st.session_state.lancer_calendrier = False
    st.rerun()


# ── Onglets ────────────────────────────────────────────────────────────────────
tab_monsite, tab_concurrents_dash, tab_blog, tab_concurrents_gestion, tab_chat = st.tabs([
    "Mon Site", "Concurrents", "Blog & Contenu", "Gérer Concurrents", "Chat IA"
])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — MON SITE
# ════════════════════════════════════════════════════════════════════════════════
with tab_monsite:
    mon_site = st.session_state.mon_site
    rapport  = st.session_state.rapport

    if not mon_site and not rapport:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown('<div class="section-title">Mon site</div>', unsafe_allow_html=True)
            st.markdown(f"""
**{SAFIA_CONTEXT['marque']}** — [{SAFIA_CONTEXT['url']}]({SAFIA_CONTEXT['url']})

L'agent va scraper votre site, l'analyser avec l'IA et le comparer à vos concurrents pour identifier :
- Vos **points forts SEO** à exploiter
- Vos **faiblesses** à corriger en priorité
- Les **quick wins** — actions à fort impact, court délai
- Les mots-clés présents et manquants
""")
            if st.button("Lancer l'analyse de mon site", use_container_width=True):
                st.session_state.lancer_mon_site = True
                st.rerun()
        with col_r:
            st.markdown('<div class="section-title">Concurrents</div>', unsafe_allow_html=True)
            st.markdown("""
Analysez aussi vos concurrents pour obtenir une comparaison complète.
Les deux analyses ensemble donnent le tableau de bord stratégique complet.
""")
            if st.button("Analyser les concurrents", use_container_width=True):
                st.session_state.lancer = True
                st.rerun()
    else:
        if mon_site:
            st.markdown('<div class="section-title">Scores SEO — safia-rugs.com</div>', unsafe_allow_html=True)
            c1, c2, c3, c4, c5 = st.columns(5)
            scores = [
                ("Score global",   mon_site.get("score_seo_global", 0), "gold"),
                ("Technique",      mon_site.get("score_technique", 0),   "blue"),
                ("Contenu",        mon_site.get("score_contenu", 0),      ""),
                ("Liens internes", mon_site.get("nb_liens", 0),           ""),
                ("Taille page",    f"{mon_site.get('taille_page_kb',0)}kb", ""),
            ]
            for col, (label, val, cls) in zip([c1,c2,c3,c4,c5], scores):
                with col:
                    st.markdown(f'<div class="kpi-card {cls}"><div class="kpi-val kpi-{cls}">{val}</div><div class="kpi-lab">{label}</div></div>', unsafe_allow_html=True)
            st.markdown("")

            alerte = mon_site.get("alerte_critique", "")
            if alerte and "aucune" not in alerte.lower():
                st.markdown(f'<div class="alert-critique">🚨 <strong>Alerte critique :</strong> {alerte}</div>', unsafe_allow_html=True)
                st.markdown("")

            col_gauche, col_droite = st.columns(2)
            with col_gauche:
                st.markdown("#### ⚡ Quick Wins — Actions immédiates")
                qws = mon_site.get("quick_wins", [])
                if qws:
                    for qw in qws:
                        impact = qw.get("impact", "moyen")
                        cls = "fort" if impact == "fort" else "moyen"
                        st.markdown(f"""
<div class="qw-card {cls}">
  <strong>{qw.get('action','')}</strong><br>
  <span style="font-size:12px;color:#888">
    Impact : <strong>{impact}</strong> &nbsp;·&nbsp;
    Effort : {qw.get('effort','—')} &nbsp;·&nbsp;
    ⏱ {qw.get('delai','—')}
  </span>
</div>""", unsafe_allow_html=True)
                else:
                    st.info("Lancez l'analyse de votre site pour voir les quick wins.")

                st.markdown("#### 🔑 Mots-clés")
                mcp = mon_site.get("mots_cles_presents", [])
                mcm = mon_site.get("mots_cles_manquants", [])
                if mcp:
                    st.markdown("**Présents :** " + " ".join(
                        f'<span style="background:#f0fdf4;color:#15803d;padding:2px 9px;border-radius:10px;font-size:11px;margin:2px;display:inline-block">{m}</span>'
                        for m in mcp
                    ), unsafe_allow_html=True)
                if mcm:
                    st.markdown("**Manquants :** " + " ".join(
                        f'<span style="background:#fff1f2;color:#dc2626;padding:2px 9px;border-radius:10px;font-size:11px;margin:2px;display:inline-block">{m}</span>'
                        for m in mcm
                    ), unsafe_allow_html=True)

            with col_droite:
                st.markdown("#### ✅ Points forts")
                for p in mon_site.get("points_forts", []):
                    st.markdown(f"- {p}")
                st.markdown("#### ⚠️ Points à améliorer")
                for p in mon_site.get("points_faibles", []):
                    st.markdown(f"- {p}")
                if mon_site.get("vs_concurrents"):
                    st.markdown("#### 🆚 Positionnement vs concurrents")
                    st.info(mon_site.get("vs_concurrents", ""))

            opts = mon_site.get("optimisations_prioritaires", [])
            if opts:
                st.markdown("---")
                st.markdown("#### 🛠️ Optimisations prioritaires")
                for opt in opts:
                    with st.expander(f"📄 {opt.get('page','—')} — {opt.get('probleme','')[:60]}"):
                        st.markdown(f"**Problème :** {opt.get('probleme','')}")
                        st.markdown(f"**Solution :** {opt.get('solution','')}")

            with st.expander("🔍 Données techniques actuelles"):
                st.markdown(f"**Title :** {mon_site.get('title','—')}")
                st.markdown(f"**H1 :** {mon_site.get('h1','—')}")
                st.markdown(f"**Meta desc :** {mon_site.get('meta_desc','—')}")
                st.markdown(f"**Schema.org :** {'✅' if mon_site.get('a_schema') else '❌'} &nbsp;·&nbsp; **Canonical :** {'✅' if mon_site.get('a_canonical') else '❌'} &nbsp;·&nbsp; **Taille :** {mon_site.get('taille_page_kb',0)}kb &nbsp;·&nbsp; **Vitesse :** {mon_site.get('vitesse_estimee','—')}")

        elif rapport:
            st.info("Analyse de safia-rugs.com non encore effectuée. Cliquez **'Analyser mon site'** dans la barre latérale.")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — DASHBOARD CONCURRENTS
# ════════════════════════════════════════════════════════════════════════════════
with tab_concurrents_dash:
    rapport = st.session_state.rapport

    if not rapport:
        st.info("Lancez l'analyse des concurrents depuis la barre latérale.")
        st.markdown("""
**Ce que l'analyse fait :**
1. Scrape chaque site concurrent (ScraperAPI, rendu JS, IP France)
2. Analyse chaque page avec Gemini AI (mots-clés, stratégie, niveau de menace)
3. Compare avec la semaine précédente (détection de changements)
4. Génère une synthèse stratégique + classement des opportunités
5. Envoie le rapport par email + log dans Google Sheets
""")
    else:
        sm = rapport.get("score_menace", 5)
        sc = "#e11d48" if sm >= 8 else "#d97706" if sm >= 6 else "#16a34a"
        lbl = "CRITIQUE" if sm >= 8 else "ÉLEVÉE" if sm >= 6 else "MODÉRÉE"
        c1, c2, c3, c4 = st.columns(4)
        kpis = [
            ("Concurrents",  rapport.get("nb_concurrents", 0), "blue"),
            ("Opportunités", rapport.get("nb_opportunites", 0), "gold"),
            ("Critiques",    rapport.get("nb_critiques", 0),    "red"),
            (f"Menace {lbl}", f"{sm}/10", ""),
        ]
        for col, (label, val, cls) in zip([c1,c2,c3,c4], kpis):
            color_override = f"color:{sc}" if label.startswith("Menace") else ""
            with col:
                st.markdown(f'<div class="kpi-card {cls}"><div class="kpi-val kpi-{cls}" style="{color_override}">{val}</div><div class="kpi-lab">{label}</div></div>', unsafe_allow_html=True)

        st.markdown("")
        scoring  = rapport.get("scoring", {})
        synthese = scoring.get("synthese", {})

        col_res, col_top = st.columns([3, 2])
        with col_res:
            st.markdown('<div class="section-title">Résumé stratégique</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="alert-info">{rapport.get("resume_executif","—")}</div>', unsafe_allow_html=True)
            st.markdown("")
            if synthese.get("tendance_dominante"):
                st.markdown(f"**📈 Tendance :** {synthese['tendance_dominante']}")
            if rapport.get("alerte_strategique") and "aucune" not in str(rapport.get("alerte_strategique","")).lower():
                st.markdown(f'<div class="alert-warning">⚠️ {rapport["alerte_strategique"]}</div>', unsafe_allow_html=True)
            st.markdown("")
            st.markdown("**✅ Actions recommandées**")
            for i, r in enumerate(synthese.get("recommandations_actionnables", [])[:5], 1):
                p = r.get("priorite","moyenne").upper()
                badge = f'<span class="badge badge-{p.lower()}">{p}</span>' if p in ("HAUTE","MOYENNE","FAIBLE") else ""
                st.markdown(f"**{i}.** {r.get('action','—')} {badge} — Impact : {r.get('impact_estime','—')}", unsafe_allow_html=True)

        with col_top:
            st.markdown('<div class="section-title">Top Opportunités</div>', unsafe_allow_html=True)
            for i, opp in enumerate(rapport.get("top_3", []), 1):
                p = opp.get("priorite","HAUTE")
                badge_cls = "critique" if p == "CRITIQUE" else "haute" if p == "HAUTE" else "moyenne"
                with st.expander(f"#{i} · {opp.get('sujet','—')} · {opp.get('score_final','')}/10"):
                    st.markdown(f'<span class="badge badge-{badge_cls}">{p}</span> &nbsp; Potentiel : {opp.get("potentiel","—")} · Intention : {opp.get("intention","—")}', unsafe_allow_html=True)
                    st.markdown(f"*{opp.get('raison','—')}*")
                    if st.button(f"Générer article", key=f"opp_art_{i}"):
                        with st.spinner("Génération du brief..."):
                            brief = generer_brief_seo(opp.get("sujet",""), opp.get("mots_cles_cibles", []))
                            st.session_state.brief_actuel = brief
                            st.session_state.agent.dernier_brief = brief
                        st.success("Brief prêt ! Allez dans Blog & Contenu → Article complet")

        st.markdown("---")
        st.markdown('<div class="section-title">Analyse détaillée</div>', unsafe_allow_html=True)
        toutes = rapport.get("toutes_analyses", [])
        if toutes:
            df = pd.DataFrame([{
                "Concurrent":      a.get("nom","—"),
                "Title":           a.get("title","—")[:50],
                "Score qualité":   a.get("score_qualite", 0),
                "Score technique": a.get("score_technique", 0),
                "Menace":          a.get("niveau_menace","—").upper(),
                "Intention":       a.get("intention_contenu","—"),
                "Changement":      a.get("comparaison",{}).get("niveau_changement","—"),
                "Alerte":          "🔴" if a.get("comparaison",{}).get("alerte") else "✅",
            } for a in toutes])
            st.dataframe(df, use_container_width=True, hide_index=True,
                column_config={
                    "Score qualité":   st.column_config.ProgressColumn(min_value=0, max_value=10),
                    "Score technique": st.column_config.ProgressColumn(min_value=0, max_value=10),
                })

        alertes = rapport.get("scoring", {}).get("alertes", [])
        if alertes:
            st.markdown("---")
            st.markdown('<div class="section-title">Changements détectés</div>', unsafe_allow_html=True)
            for a in alertes:
                st.markdown(f'<div class="alert-warning">⚠️ <strong>{a["nom"]}</strong> — Changement {a["niveau"]} — Urgence : {a.get("urgence","—")}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — BLOG & CONTENU
# ════════════════════════════════════════════════════════════════════════════════
with tab_blog:
    st.markdown(f'<div class="section-title">Blog « {SAFIA_CONTEXT["blog_nom"]} »</div>', unsafe_allow_html=True)

    blog_tab1, blog_tab2, blog_tab3, blog_tab4 = st.tabs([
        "Sujets", "Brief SEO", "Article complet", "Calendrier"
    ])

    # ── Sujets ─────────────────────────────────────────────────────────────────
    with blog_tab1:
        col_btn, col_info = st.columns([2, 3])
        with col_btn:
            if st.button("Générer 10 sujets optimisés", use_container_width=True):
                with st.spinner("Analyse des opportunités concurrentielles..."):
                    analyses = st.session_state.rapport.get("toutes_analyses", []) if st.session_state.rapport else []
                    st.session_state.sujets_blog = suggerer_sujets_blog(analyses, nb=10)
        with col_info:
            st.caption(f"Sujets générés en tenant compte de vos concurrents, mots-clés prioritaires et du blog « {SAFIA_CONTEXT['blog_nom']} ».")

        sujets = st.session_state.sujets_blog
        if sujets:
            for i, s in enumerate(sujets, 1):
                prio = s.get("priorite","P2")
                p_ico = "🔴" if prio=="P1" else "🟡" if prio=="P2" else "⚪"
                pot   = s.get("potentiel_conversion","moyen")
                conv_ico = "💰" if pot=="fort" else "📈" if pot=="moyen" else "📖"
                with st.container():
                    c_main, c_btn = st.columns([6, 1])
                    with c_main:
                        st.markdown(f"""
<div class="blog-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
    <strong style="font-size:15px;color:#080f20">{p_ico} #{i} — {s.get('titre','')}</strong>
    <span style="font-size:11px;color:#aaa;white-space:nowrap">{s.get('type_contenu','')}</span>
  </div>
  <div style="font-size:12px;color:#666;margin-bottom:6px">🎯 {', '.join(s.get('mots_cles_cibles',[]))}</div>
  <div style="font-size:11px;color:#aaa">
    📊 ~{s.get('volume_mensuel_estime','?')}/mois &nbsp;·&nbsp;
    {conv_ico} Conversion {pot} &nbsp;·&nbsp; ⏱ {s.get('effort_redaction','—')}
  </div>
  <div style="font-size:12px;color:#b8872a;margin-top:6px">💡 {s.get('pourquoi','')}</div>
</div>
""", unsafe_allow_html=True)
                    with c_btn:
                        st.markdown("<br><br>", unsafe_allow_html=True)
                        if st.button("Brief →", key=f"brief_{i}", use_container_width=True):
                            with st.spinner("Génération du brief..."):
                                brief = generer_brief_seo(s.get("titre",""), s.get("mots_cles_cibles",[]))
                                st.session_state.brief_actuel = brief
                                st.session_state.agent.dernier_brief = brief
                            st.success("Brief généré !")
                            st.rerun()
        else:
            st.info("Cliquez sur **Générer 10 sujets** pour obtenir des idées d'articles personnalisées.")

    # ── Brief ──────────────────────────────────────────────────────────────────
    with blog_tab2:
        with st.form("form_brief"):
            c1, c2 = st.columns([3, 1])
            with c1: sujet_b = st.text_input("Sujet de l'article", placeholder="Ex: Comment entretenir un tapis berbère en laine")
            with c2: mots_b  = st.text_input("Mots-clés (optionnel)", placeholder="tapis, entretien...")
            if st.form_submit_button("Générer le brief SEO", use_container_width=True):
                if sujet_b:
                    with st.spinner("Génération..."):
                        mots = [m.strip() for m in mots_b.split(",")] if mots_b else SAFIA_CONTEXT["mots_cles_p1"]
                        brief = generer_brief_seo(sujet_b, mots)
                        st.session_state.brief_actuel = brief
                        st.session_state.agent.dernier_brief = brief

        brief = st.session_state.brief_actuel
        if brief:
            st.markdown("---")
            st.markdown(f"### {brief.get('titre_h1', brief.get('titre_seo',''))}")
            col_m, col_k = st.columns(2)
            with col_m:
                st.code(f"Title : {brief.get('titre_seo','')}", language=None)
                st.code(f"Meta  : {brief.get('meta_description','')}", language=None)
                st.code(f"URL   : {SAFIA_CONTEXT['blog_slug_prefix']}{brief.get('url_slug','')}", language=None)
                st.markdown(f"⏱ {brief.get('temps_lecture_estime','')} · {brief.get('longueur_cible_mots','')} mots · {brief.get('intention_recherche','')}")
            with col_k:
                st.markdown("**Mots-clés principaux :**")
                st.markdown(" ".join(f'<span style="background:#eff6ff;color:#2563eb;padding:2px 9px;border-radius:8px;font-size:11px;margin:2px;display:inline-block">{m}</span>' for m in brief.get("mots_cles_principaux",[])), unsafe_allow_html=True)
                st.markdown("**Longue traîne :**")
                st.markdown(" ".join(f'<span style="background:#fffbeb;color:#b45309;padding:2px 9px;border-radius:8px;font-size:11px;margin:2px;display:inline-block">{m}</span>' for m in brief.get("mots_cles_longue_traine",[])), unsafe_allow_html=True)

            st.markdown("**📐 Structure :**")
            for s in brief.get("structure",[]):
                badge_h = "🔷" if s.get("niveau")=="H2" else "🔹"
                st.markdown(f"{badge_h} `{s.get('niveau','H2')}` **{s.get('titre','')}** — *{s.get('contenu_attendu','')}*")

            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                if brief.get("faq_schema"):
                    st.markdown("**❓ FAQ Schema**")
                    for f in brief.get("faq_schema",[]):
                        with st.expander(f.get("question","")):
                            st.write(f.get("reponse_courte",""))
            with col_ex2:
                st.markdown(f"**💡 Angle :** {brief.get('angle_differentiant','')}")
                st.markdown(f"**🔗 Liens internes :** {', '.join(brief.get('liens_internes',[]))}")
                if brief.get("notes_redacteur"):
                    st.info(f"📝 {brief['notes_redacteur']}")

            c_dl, c_gen = st.columns(2)
            with c_dl:
                st.download_button("⬇️ Brief JSON", json.dumps(brief, ensure_ascii=False, indent=2),
                    file_name=f"brief_{brief.get('url_slug','')}.json", mime="application/json")
            with c_gen:
                if st.button("Générer l'article complet", use_container_width=True):
                    with st.spinner("Rédaction en cours (30-60s)..."):
                        article = generer_article_complet(brief)
                        st.session_state.article_actuel = article
                    st.success("Article généré !")
                    st.rerun()

    # ── Article ────────────────────────────────────────────────────────────────
    with blog_tab3:
        with st.form("form_article_direct"):
            c1, c2 = st.columns([4, 1])
            with c1: sujet_a = st.text_input("Sujet", placeholder="Guide complet pour choisir un tapis Azilal")
            with c2:
                st.markdown("<br>", unsafe_allow_html=True)
                gen_a = st.form_submit_button("🚀 Générer", use_container_width=True)
        if gen_a and sujet_a:
            with st.spinner("Création du brief puis rédaction (45-90s)..."):
                brief_auto = generer_brief_seo(sujet_a, SAFIA_CONTEXT["mots_cles_p1"])
                st.session_state.brief_actuel = brief_auto
                st.session_state.agent.dernier_brief = brief_auto
                article = generer_article_complet(brief_auto)
                st.session_state.article_actuel = article

        article = st.session_state.article_actuel
        brief   = st.session_state.brief_actuel
        if article:
            if brief:
                st.markdown(f"**Title :** `{brief.get('titre_seo','')}`  \n**URL :** `{SAFIA_CONTEXT['blog_slug_prefix']}{brief.get('url_slug','')}`")
                st.markdown("---")
            col_prev, col_raw = st.columns(2)
            with col_prev:
                st.markdown("**👁️ Aperçu**")
                st.markdown(article)
            with col_raw:
                st.markdown("**📋 Markdown brut** (copier dans Shopify)")
                st.text_area("", value=article, height=550, label_visibility="collapsed", key="art_raw")
            slug = brief.get("url_slug","article") if brief else "article"
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇️ Markdown", article, f"{slug}.md", "text/markdown")
            with c2:
                st.download_button("⬇️ HTML", f"<article>{article}</article>", f"{slug}.html", "text/html")
        elif st.session_state.brief_actuel:
            st.info("Brief prêt. Allez dans **Brief SEO** et cliquez *Générer l'article complet*.")
        else:
            st.info("Entrez un sujet ci-dessus ou générez d'abord un sujet dans l'onglet **Sujets**.")

    # ── Calendrier ─────────────────────────────────────────────────────────────
    with blog_tab4:
        col_c1, col_c2 = st.columns([2, 3])
        with col_c1:
            nb_sem = st.slider("Nombre de semaines", 2, 8, 4)
            if st.button("Générer le calendrier", use_container_width=True):
                with st.spinner("Génération du plan de contenu..."):
                    analyses = st.session_state.rapport.get("toutes_analyses", []) if st.session_state.rapport else []
                    st.session_state.calendrier = generer_calendrier_contenu(nb_semaines=nb_sem, analyses=analyses)
        with col_c2:
            st.caption(f"Le calendrier planifie les prochains articles pour le blog **{SAFIA_CONTEXT['blog_nom']}**, basé sur les opportunités SEO détectées.")

        cal = st.session_state.calendrier
        if cal:
            st.markdown(f"**{len(cal)} articles planifiés :**")
            for idx, item in enumerate(cal):
                prio_ico = "🔴" if item.get("priorite")=="haute" else "🟡"
                with st.expander(f"📅 **{item.get('date_publication','Sem.'+ str(item.get('semaine','?')))}** — {item.get('titre','')} {prio_ico}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Type :** {item.get('type','—')} · {item.get('intention','—')}")
                        st.markdown(f"**Volume :** ~{item.get('volume_estime','?')}/mois · **Effort :** {item.get('effort','—')}")
                        st.markdown(f"**CTA :** {item.get('cta_principal','—')}")
                        st.markdown(f"**URL :** `{SAFIA_CONTEXT['blog_slug_prefix']}{item.get('slug_url','')}`")
                    with c2:
                        st.markdown("**Mots-clés :** " + ", ".join(item.get("mots_cles",[])))
                        st.markdown(f"**Angle :** *{item.get('angle','')}*")
                    if st.button(f"Brief pour cet article", key=f"cal_brief_{idx}"):
                        with st.spinner("Génération du brief..."):
                            brief = generer_brief_seo(item.get("titre",""), item.get("mots_cles",[]))
                            st.session_state.brief_actuel = brief
                            st.session_state.agent.dernier_brief = brief
                        st.success("Brief généré !")

            df_cal = pd.DataFrame([{
                "Date":      c.get("date_publication",""),
                "Titre":     c.get("titre",""),
                "Type":      c.get("type",""),
                "Mots-clés": ", ".join(c.get("mots_cles",[])),
                "Volume":    c.get("volume_estime",""),
                "Effort":    c.get("effort",""),
                "URL":       f"{SAFIA_CONTEXT['blog_slug_prefix']}{c.get('slug_url','')}",
            } for c in cal])
            st.download_button("⬇️ Exporter le calendrier (CSV)", df_cal.to_csv(index=False, encoding="utf-8-sig"),
                "calendrier_contenu_safia.csv", "text/csv")
        else:
            st.info("Cliquez **Générer le calendrier** pour planifier vos prochains articles.")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — GÉRER CONCURRENTS
# ════════════════════════════════════════════════════════════════════════════════
with tab_concurrents_gestion:
    st.markdown('<div class="section-title">Gérer les concurrents surveillés</div>', unsafe_allow_html=True)

    with st.expander("➕ Ajouter un concurrent", expanded=True):
        with st.form("form_ajout", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 3, 1])
            with c1: nn = st.text_input("Nom du site", placeholder="Berbère Market")
            with c2: nu = st.text_input("URL complète", placeholder="https://berbere-market.com")
            with c3: nc = st.selectbox("Catégorie", ["e-commerce", "blog SEO", "marketplace", "marque"])
            if st.form_submit_button("➕ Ajouter", use_container_width=True):
                if nn and nu:
                    if not nu.startswith("http"):
                        st.error("URL doit commencer par https://")
                    else:
                        with st.spinner("..."):
                            ok = ajouter_concurrent(nn, nu.strip(), nc)
                        st.success(f"✅ **{nn}** ajouté !") if ok else st.warning("Déjà présent ou erreur.")
                        st.rerun()
                else:
                    st.warning("Remplissez nom et URL.")

    st.markdown("---")
    with st.spinner("Chargement..."):
        tous = lire_tous_concurrents()

    if tous:
        actifs   = [c for c in tous if c["statut"] == "actif"]
        inactifs = [c for c in tous if c["statut"] != "actif"]
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-val">{len(tous)}</div><div class="kpi-lab">Total</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="kpi-card green"><div class="kpi-val kpi-green">{len(actifs)}</div><div class="kpi-lab">Actifs</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-val" style="color:#bbb">{len(inactifs)}</div><div class="kpi-lab">Inactifs</div></div>', unsafe_allow_html=True)
        st.markdown("")

        if actifs:
            st.markdown("**🟢 Actifs**")
            for c in actifs:
                cc1, cc2, cc3, cc4 = st.columns([2, 3, 1, 1])
                with cc1: st.markdown(f"**{c['nom']}**")
                with cc2: st.markdown(f"[{c['url']}]({c['url']})")
                with cc3: st.markdown(f"`{c['categorie']}`")
                with cc4:
                    if st.button("⏸", key=f"d_{c['url']}", help="Désactiver", use_container_width=True):
                        desactiver_concurrent(c["url"]); st.rerun()
        if inactifs:
            st.markdown("**⚫ Inactifs**")
            for c in inactifs:
                cc1, cc2, cc3, cc4 = st.columns([2, 3, 1, 1])
                with cc1: st.markdown(f"~~{c['nom']}~~")
                with cc2: st.markdown(f"[{c['url']}]({c['url']})")
                with cc3: st.markdown(f"`{c['categorie']}`")
                with cc4:
                    if st.button("▶", key=f"r_{c['url']}", help="Réactiver", use_container_width=True):
                        reactiver_concurrent(c["url"]); st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# TAB 5 — CHAT IA
# ════════════════════════════════════════════════════════════════════════════════
with tab_chat:
    st.markdown('<div class="section-title">Chat avec votre agent SEO</div>', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown(f"""
<div class="alert-info">
  Bonjour ! Je suis votre agent SEO spécialisé <strong>Safia Rugs</strong>.<br><br>
  Je peux vous aider à :<br>
  · <strong>Analyser</strong> vos concurrents et identifier les opportunités<br>
  · <strong>Rédiger</strong> des articles pour le blog <em>« {SAFIA_CONTEXT['blog_nom']} »</em><br>
  · <strong>Stratégie SEO</strong> — mots-clés, maillage interne, optimisations<br><br>
  Essayez : <em>"Rédige un article sur les tapis Azilal"</em> ou <em>"Suggère des sujets de blog"</em>
</div>
""", unsafe_allow_html=True)
        st.markdown("")

    for msg in st.session_state.messages:
        css = "chat-user" if msg["role"] == "user" else "chat-agent"
        ico = "🧑" if msg["role"] == "user" else "🤖"
        st.markdown(f'<div class="{css}">{ico} {msg["content"]}</div>', unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            inp = st.text_input("", placeholder=f"Posez votre question SEO ou demandez un article pour le blog « {SAFIA_CONTEXT['blog_nom']} »...", label_visibility="collapsed")
        with c2:
            send = st.form_submit_button("Envoyer", use_container_width=True)

    if send and inp:
        st.session_state.messages.append({"role": "user", "content": inp})
        with st.spinner("Réflexion..."):
            rep = st.session_state.agent.chat(inp)
        st.session_state.messages.append({"role": "assistant", "content": rep})
        st.rerun()

    st.markdown("---")
    cols = st.columns(4)
    shortcuts = [
        ("Sujets blog",    "Suggère 8 sujets d'articles pour le blog Conseils de Safae"),
        ("Opportunités",   "Quelles sont les meilleures opportunités SEO à exploiter maintenant ?"),
        ("Article Azilal", "Rédige un article complet sur les tapis Azilal"),
        ("Effacer",        None),
    ]
    for col, (label, question) in zip(cols, shortcuts):
        with col:
            if st.button(label, use_container_width=True):
                if question:
                    st.session_state.messages.append({"role": "user", "content": question})
                    rep = st.session_state.agent.chat(question)
                    st.session_state.messages.append({"role": "assistant", "content": rep})
                else:
                    st.session_state.messages = []
                st.rerun()

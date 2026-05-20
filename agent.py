"""
Agent SEO IA — Safia Rugs
Agent Python autonome · OpenRouter (Gemini 2.0 Flash) · Google Sheets · ScraperAPI
"""

import os, json, re, requests, gspread, smtplib
from datetime import datetime, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2.service_account import Credentials
from typing import Optional

# ──────────────────────────────────────────────
# CONFIG — variables d'environnement (.env)
# ──────────────────────────────────────────────
OPENROUTER_API_KEY    = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL      = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
SCRAPER_API_KEY       = os.getenv("SCRAPER_API_KEY", "")
SHEETS_ID             = os.getenv("SHEETS_ID", "")
GMAIL_USER            = os.getenv("GMAIL_USER", "")
GMAIL_PASSWORD        = os.getenv("GMAIL_PASSWORD", "")
GOOGLE_CREDS_FILE     = os.getenv("GOOGLE_CREDS_FILE", "google_credentials.json")
RAPPORT_DESTINATAIRE  = os.getenv("RAPPORT_DESTINATAIRE", "")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://safia-rugs.com",
    "X-Title": "Safia Rugs SEO Agent",
}

# ──────────────────────────────────────────────
# CONTEXTE SAFIA RUGS — données réelles issues de la stratégie SEO
# ──────────────────────────────────────────────
SAFIA_CONTEXT = {
    # ── Identité marque ──────────────────────────────
    "marque":         "Safia Rugs",
    "fondatrice":     "Safae",
    "tagline":        "Voyagez depuis votre salon",
    "url":            "https://safia-rugs.com",
    "boutique":       "Shopify — safia-rugs.com",
    "livraison":      "Livraison tapis gratuite en 3 jours",

    # ── Blog ────────────────────────────────────────
    "blog_nom":          "Conseils de Safae",
    "blog_url":          "https://safia-rugs.com/blogs/conseils-de-safae/",
    "blog_slug_prefix":  "/blogs/conseils-de-safae/",

    # ── Navigation réelle du site ────────────────────
    "navigation": [
        "Tapis berbère sur mesure",
        "Tapis berbère",
        "Maroquinerie",
        "Mon combat",
        "Conseils de Safae",
        "Professionnel",
        "Écrivez-nous",
        "Safia Chez Vous",
    ],
    "collections": {
        "tapis_berbere_sur_mesure": "https://safia-rugs.com/collections/tapis-berbere-sur-mesure",
        "tapis_berbere":            "https://safia-rugs.com/collections/tapis-berbere",
        "maroquinerie":             "https://safia-rugs.com/collections/maroquinerie",
    },
    "pages_cles": {
        "mon_combat":    "https://safia-rugs.com/pages/mon-combat",
        "safia_chez_vous": "https://safia-rugs.com/pages/safia-chez-vous",
        "professionnel": "https://safia-rugs.com/pages/professionnel",
    },

    # ── Marché & audience ───────────────────────────
    "marches":   ["France", "Maroc"],
    "audience":  "femmes 25-50 ans, passionnées de décoration intérieure authentique, cherchant des pièces berbères artisanales uniques pour sublimer leur intérieur",
    "usp":       "Tapis berbères 100% artisanaux fabriqués par des artisans marocains, livraison gratuite en 3 jours — chaque pièce est unique",
    "ton":       "élégant, chaleureux, authentique, comme une amie experte en décoration marocaine qui partage ses conseils avec passion",

    # ── Mots-clés ────────────────────────────────────
    "mots_cles_p1": [
        "tapis berbère", "tapis berbère marocain", "tapis berbère sur mesure",
        "tapis marocain", "tapis azilal", "tapis boucherouite",
        "maroquinerie marocaine", "décoration berbère",
    ],
    "mots_cles_p2": [
        "tapis kilim", "tapis berber laine", "tapis fait main maroc",
        "tapis marocain salon", "décoration bohème marocaine",
        "artisanat berbère", "tapis marrakech", "tapis authentique maroc",
    ],
    "villes_seo_france": ["Paris", "Lyon", "Marseille", "Bordeaux", "Toulouse"],
    "villes_seo_maroc":  ["Casablanca", "Rabat", "Marrakech", "Fès", "Agadir"],

    # ── Catégories produits ──────────────────────────
    "categories": [
        "Tapis berbère sur mesure",
        "Tapis berbère",
        "Maroquinerie",
    ],

    # ── Concurrents ──────────────────────────────────
    "concurrents_principaux": ["Tribaliste", "Mazir", "Tamazi", "Them", "Secret Berbère"],

    # ── Contenu blog existant ────────────────────────
    "articles_blog_existants": [
        "Comment choisir un tapis berbère : guide complet 2026",
        "Tapis Azilal vs Boucherouite : quelles différences ?",
        "10 idées déco pour intégrer un tapis berbère dans votre salon",
    ],
}

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────
def semaine_iso() -> str:
    d = date.today()
    return f"{d.year}-S{d.isocalendar()[1]:02d}"

def _appeler_openrouter(messages: list, temperature: float, max_tokens: int, json_mode: bool = False) -> str:
    """Appel bas niveau OpenRouter — retourne le texte brut de la réponse."""
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    r = requests.post(OPENROUTER_URL, headers=OPENROUTER_HEADERS, json=payload, timeout=90)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def appeler_gemini(prompt: str, temperature: float = 0.3, max_tokens: int = 2000) -> dict:
    """Appel IA via OpenRouter — retourne un dict JSON parsé."""
    messages = [
        {"role": "system", "content": "Tu es un expert SEO. Réponds UNIQUEMENT en JSON valide, sans texte autour."},
        {"role": "user",   "content": prompt},
    ]
    text = _appeler_openrouter(messages, temperature, max_tokens, json_mode=True)
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)

def appeler_gemini_texte(prompt: str, temperature: float = 0.5, max_tokens: int = 3000) -> str:
    """Appel IA via OpenRouter — retourne du texte libre (chat, articles)."""
    messages = [{"role": "user", "content": prompt}]
    return _appeler_openrouter(messages, temperature, max_tokens, json_mode=False)

# ──────────────────────────────────────────────
# OUTIL 1 : GOOGLE SHEETS
# ──────────────────────────────────────────────
def get_sheets_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_FILE, scopes=scopes)
    return gspread.authorize(creds)

def _ws_concurrents():
    gc = get_sheets_client()
    sh = gc.open_by_key(SHEETS_ID)
    return sh.worksheet("Concurrents")

def lire_concurrents() -> list[dict]:
    """Lit uniquement les concurrents actifs."""
    try:
        rows = _ws_concurrents().get_all_records()
        return [
            {
                "nom":       r.get("Nom du concurrent", r.get("nom", "")),
                "url":       r.get("URL complète", r.get("url", "")),
                "categorie": r.get("Catégorie", r.get("categorie", "")),
            }
            for r in rows
            if str(r.get("Statut", r.get("statut", "actif"))).lower() == "actif"
            and (r.get("Nom du concurrent") or r.get("nom"))
        ]
    except Exception as e:
        print(f"[SHEETS] Erreur lecture concurrents: {e}")
        return []

def lire_tous_concurrents() -> list[dict]:
    """Lit tous les concurrents (actifs + inactifs) pour la gestion."""
    try:
        rows = _ws_concurrents().get_all_records()
        return [
            {
                "nom":        r.get("Nom du concurrent", r.get("nom", "")),
                "url":        r.get("URL complète", r.get("url", "")),
                "categorie":  r.get("Catégorie", r.get("categorie", "e-commerce")),
                "statut":     str(r.get("Statut", r.get("statut", "actif"))).lower(),
                "date_ajout": str(r.get("Date d'ajout", "")),
            }
            for r in rows
            if r.get("Nom du concurrent") or r.get("nom")
        ]
    except Exception as e:
        print(f"[SHEETS] Erreur lecture tous concurrents: {e}")
        return []

def ajouter_concurrent(nom: str, url: str, categorie: str = "e-commerce") -> bool:
    """Ajoute un nouveau concurrent dans Google Sheets."""
    try:
        ws = _ws_concurrents()
        # Vérifier que l'URL n'existe pas déjà
        existants = ws.get_all_records()
        for r in existants:
            if r.get("URL complète", r.get("url", "")) == url:
                return False  # déjà présent
        ws.append_row([nom, url, categorie, "actif", str(date.today())])
        print(f"[SHEETS] Concurrent ajouté : {nom}")
        return True
    except Exception as e:
        print(f"[SHEETS] Erreur ajout concurrent: {e}")
        return False

def _changer_statut_concurrent(url: str, nouveau_statut: str) -> bool:
    """Change le statut d'un concurrent (actif/inactif)."""
    try:
        ws = _ws_concurrents()
        rows = ws.get_all_values()
        for i, row in enumerate(rows[1:], start=2):
            if len(row) >= 2 and row[1] == url:
                ws.update_cell(i, 4, nouveau_statut)
                return True
        return False
    except Exception as e:
        print(f"[SHEETS] Erreur changement statut: {e}")
        return False

def desactiver_concurrent(url: str) -> bool:
    return _changer_statut_concurrent(url, "inactif")

def reactiver_concurrent(url: str) -> bool:
    return _changer_statut_concurrent(url, "actif")

def lire_snapshots_historique() -> list[dict]:
    """Lit l'historique des snapshots pour comparaison N vs N-1."""
    try:
        gc = get_sheets_client()
        sh = gc.open_by_key(SHEETS_ID)
        ws = sh.worksheet("snapshots_concurrents")
        return ws.get_all_records()
    except Exception as e:
        print(f"[SHEETS] Erreur lecture snapshots: {e}")
        return []

def ecrire_snapshot(data: dict):
    """Écrit un snapshot concurrent dans Google Sheets."""
    try:
        gc = get_sheets_client()
        sh = gc.open_by_key(SHEETS_ID)
        ws = sh.worksheet("snapshots_concurrents")
        row = [
            data.get("semaine_iso", ""),
            data.get("date_scraping", ""),
            data.get("nom", ""),
            data.get("url", ""),
            data.get("categorie", ""),
            data.get("title", ""),
            data.get("h1", ""),
            data.get("h2s", ""),
            data.get("meta_desc", ""),
            ", ".join(data.get("mots_cles_principaux", [])),
            data.get("intention_contenu", ""),
            data.get("angle_editorial", ""),
            data.get("strategie_seo", ""),
            data.get("resume_page", ""),
            str(data.get("score_qualite", "")),
            " | ".join(data.get("points_forts", [])),
            " | ".join(data.get("opportunites", [])),
            str(data.get("nb_liens", "")),
            str(data.get("a_schema", "")),
        ]
        ws.append_row(row)
        print(f"[SHEETS] Snapshot écrit: {data.get('nom')}")
    except Exception as e:
        print(f"[SHEETS] Erreur écriture snapshot: {e}")

def ecrire_log_rapport(data: dict):
    """Log le rapport hebdo dans Google Sheets."""
    try:
        gc = get_sheets_client()
        sh = gc.open_by_key(SHEETS_ID)
        ws = sh.worksheet("rapports_hebdo")
        ws.append_row([
            data.get("semaine_iso", ""),
            data.get("date_rapport", ""),
            str(data.get("nb_concurrents", "")),
            str(data.get("nb_opportunites", "")),
            str(data.get("nb_critiques", "")),
            str(data.get("score_menace", "")),
        ])
    except Exception as e:
        print(f"[SHEETS] Erreur log rapport: {e}")

# ──────────────────────────────────────────────
# OUTIL 2 : SCRAPING
# ──────────────────────────────────────────────
def scraper_page(url: str) -> str:
    """Scrape une page via ScraperAPI avec rendu JS."""
    try:
        scraper_url = f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={requests.utils.quote(url)}&render=true&country_code=fr"
        r = requests.get(scraper_url, timeout=45)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[SCRAPER] Erreur {url}: {e}")
        return ""

def parser_html(html: str, concurrent: dict) -> dict:
    """Parse le HTML et extrait les données SEO."""
    def clean(s):
        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', s or '')).strip()

    url, nom, categorie = concurrent["url"], concurrent["nom"], concurrent.get("categorie", "")

    if not html or len(html) < 200:
        return {
            "url": url, "nom": nom, "categorie": categorie,
            "erreur": "HTML vide", "title": "Non accessible",
            "h1": "Non accessible", "h2s": "", "h3s": "", "meta_desc": "",
            "meta_keywords": "", "og_title": "", "texte_brut": "",
            "nb_liens": 0, "nb_images": 0, "a_schema": False,
            "a_canonical": False, "taille_page_kb": 0, "vitesse_estimee": "inconnue",
            "date_scraping": datetime.utcnow().isoformat(), "semaine_iso": semaine_iso()
        }

    title_m  = re.search(r'<title[^>]*>([^<]{1,200})</title>', html, re.I)
    h1_m     = re.search(r'<h1[^>]*>([\s\S]{1,400}?)</h1>', html, re.I)
    h2_ms    = re.findall(r'<h2[^>]*>([\s\S]{1,200}?)</h2>', html, re.I)
    h3_ms    = re.findall(r'<h3[^>]*>([\s\S]{1,150}?)</h3>', html, re.I)
    meta_m   = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']{1,500})', html, re.I)
    meta_m   = meta_m or re.search(r'<meta[^>]+content=["\']([^"\']{1,500})["\'][^>]+name=["\']description["\']', html, re.I)
    kw_m     = re.search(r'<meta[^>]+name=["\']keywords["\'][^>]+content=["\']([^"\']{1,300})', html, re.I)
    og_m     = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']{1,200})', html, re.I)

    texte = re.sub(r'<script[\s\S]*?</script>', ' ', html, flags=re.I)
    texte = re.sub(r'<style[\s\S]*?</style>', ' ', texte, flags=re.I)
    texte = re.sub(r'<(nav|footer|header)[\s\S]*?</\1>', ' ', texte, flags=re.I)
    texte = re.sub(r'<[^>]+>', ' ', texte)
    texte = re.sub(r'\s+', ' ', texte).strip()[:5000]

    nb_liens  = len(re.findall(r'href=["\'][^"\']*["\']', html, re.I))
    nb_images = len(re.findall(r'<img[^>]+>', html, re.I))

    return {
        "url": url, "nom": nom, "categorie": categorie,
        "title":         clean(title_m.group(1)) if title_m else "Non trouvé",
        "h1":            clean(h1_m.group(1))    if h1_m    else "Non trouvé",
        "h2s":           " | ".join([clean(h) for h in h2_ms[:8] if clean(h)]),
        "h3s":           " | ".join([clean(h) for h in h3_ms[:5] if clean(h)]),
        "meta_desc":     clean(meta_m.group(1)) if meta_m else "Non trouvée",
        "meta_keywords": clean(kw_m.group(1))   if kw_m   else "",
        "og_title":      clean(og_m.group(1))   if og_m   else "",
        "texte_brut":    texte,
        "nb_liens":      nb_liens,
        "nb_images":     nb_images,
        "a_schema":      "schema.org" in html,
        "a_canonical":   'rel="canonical"' in html or "rel='canonical'" in html,
        "taille_page_kb": round(len(html) / 1024),
        "vitesse_estimee": "rapide" if len(html) < 100000 else "moyenne" if len(html) < 300000 else "lente",
        "date_scraping": datetime.utcnow().isoformat(),
        "semaine_iso":   semaine_iso()
    }

# ──────────────────────────────────────────────
# OUTIL 3 : ANALYSE IA
# ──────────────────────────────────────────────
def analyser_page_ia(page_data: dict) -> dict:
    """Analyse une page avec Gemini et retourne une analyse SEO structurée."""
    prompt = f"""Tu es un expert SEO senior sur le marché français et marocain.
Analyse cette page web concurrente. Retourne UNIQUEMENT du JSON valide.

Concurrent : {page_data['nom']} ({page_data.get('categorie','')})
URL : {page_data['url']}
Title : {page_data.get('title','')}
H1 : {page_data.get('h1','')}
H2s : {page_data.get('h2s','')}
H3s : {page_data.get('h3s','')}
Meta desc : {page_data.get('meta_desc','')}
Schema.org : {page_data.get('a_schema',False)}
Canonical : {page_data.get('a_canonical',False)}
Nb liens : {page_data.get('nb_liens',0)}
Taille : {page_data.get('taille_page_kb',0)}kb
Contenu : {page_data.get('texte_brut','')[:3000]}

JSON attendu :
{{
  "mots_cles_principaux": ["mot1","mot2","mot3","mot4","mot5"],
  "mots_cles_secondaires": ["mot4","mot5","mot6"],
  "mots_cles_longue_traine": ["expression 1","expression 2"],
  "intention_contenu": "informationnelle|commerciale|transactionnelle|mixte",
  "angle_editorial": "description en 1 phrase",
  "strategie_seo_probable": "analyse en 2-3 phrases",
  "resume_page": "résumé objectif en 3 phrases",
  "score_qualite_contenu": 7,
  "score_technique_seo": 6,
  "points_forts_seo": ["force1","force2","force3"],
  "points_faibles_seo": ["faiblesse1","faiblesse2"],
  "opportunites_detectees": ["opportunité1","opportunité2","opportunité3"],
  "type_audience_cible": "description précise",
  "ton_editorial": "professionnel|decontracte|technique|commercial|pedagogique",
  "niveau_menace_concurrentielle": "faible|moyen|eleve|critique"
}}"""
    try:
        r = appeler_gemini(prompt, temperature=0.2, max_tokens=1500)
        return r
    except Exception as e:
        print(f"[GEMINI] Erreur analyse {page_data['nom']}: {e}")
        return {
            "mots_cles_principaux": [], "mots_cles_secondaires": [],
            "mots_cles_longue_traine": [], "intention_contenu": "mixte",
            "angle_editorial": "", "strategie_seo_probable": "",
            "resume_page": "Analyse indisponible", "score_qualite_contenu": 5,
            "score_technique_seo": 5, "points_forts_seo": [], "points_faibles_seo": [],
            "opportunites_detectees": [], "type_audience_cible": "",
            "ton_editorial": "professionnel", "niveau_menace_concurrentielle": "moyen"
        }

# ──────────────────────────────────────────────
# OUTIL 4 : DIFF N vs N-1
# ──────────────────────────────────────────────
def calculer_diff(actuel: dict, historique: list[dict]) -> dict:
    """Compare le snapshot actuel avec le précédent pour détecter les changements."""
    tries = [
        h for h in historique
        if (h.get("URL") or h.get("url")) == actuel["url"]
    ]
    tries.sort(
        key=lambda h: h.get("Date scraping\n(ISO 8601)") or h.get("date_scraping") or "",
        reverse=True
    )
    precedent = tries[1] if len(tries) > 1 else None

    if not precedent:
        return {
            "disponible": False,
            "message": "Premier snapshot",
            "niveau_changement": "non_applicable",
            "alerte": False,
            "changements": [], "nouveaux_mots_cles": [], "mots_cles_disparus": [],
            "evolution_score": 0
        }

    changements = []
    title_av = precedent.get("Title <title>") or precedent.get("title", "")
    if actuel.get("title") != title_av and title_av:
        changements.append({"champ": "Title", "avant": title_av, "apres": actuel.get("title"), "importance": "haute"})

    h1_av = precedent.get("H1") or precedent.get("h1", "")
    if actuel.get("h1") != h1_av and h1_av:
        changements.append({"champ": "H1", "avant": h1_av, "apres": actuel.get("h1"), "importance": "haute"})

    mots_actuels = actuel.get("mots_cles_principaux", [])
    mots_av_raw  = precedent.get("Mots-clés principaux (IA)") or precedent.get("mots_cles_principaux", "")
    mots_av      = mots_av_raw.split(", ") if isinstance(mots_av_raw, str) else (mots_av_raw or [])
    mots_av      = [m for m in mots_av if m]

    nouveaux = [m for m in mots_actuels if m not in mots_av]
    disparus = [m for m in mots_av if m not in mots_actuels]

    score_av = int(precedent.get("Score qualité\n(1-10)") or precedent.get("score_qualite") or 5)
    evolution_score = actuel.get("score_qualite", 5) - score_av

    nb = len(changements) + len(nouveaux)
    niveau = "aucun" if nb == 0 else "mineur" if nb <= 2 else "modéré" if nb <= 5 else "majeur"
    alerte = niveau in ("modéré", "majeur")

    return {
        "disponible": True,
        "semaine_precedente": precedent.get("Semaine ISO\n(ex: 2025-S02)") or precedent.get("semaine_iso", "N-1"),
        "changements": changements,
        "nouveaux_mots_cles": nouveaux,
        "mots_cles_disparus": disparus,
        "niveau_changement": niveau,
        "alerte": alerte,
        "evolution_score": evolution_score
    }

# ──────────────────────────────────────────────
# OUTIL 5 : INTERPRÉTER CHANGEMENTS
# ──────────────────────────────────────────────
def interpreter_changements(analyse: dict) -> dict:
    comp = analyse.get("comparaison", {})
    if not comp.get("disponible"):
        return {"interpretation_changements": "Premier snapshot", "urgence": "aucune"}

    prompt = f"""Tu es consultant SEO expert. Interprète ces changements SEO.
Retourne UNIQUEMENT du JSON valide.

Concurrent : {analyse['nom']} ({analyse['url']})
Niveau changement : {comp['niveau_changement']}
Changements : {json.dumps(comp['changements'], ensure_ascii=False)}
Nouveaux mots-clés : {', '.join(comp['nouveaux_mots_cles']) or 'aucun'}
Mots disparus : {', '.join(comp['mots_cles_disparus']) or 'aucun'}
Évolution score : {comp['evolution_score']:+d}

JSON attendu :
{{
  "interpretation_changements": "explication claire en 2 phrases",
  "signal_strategique": "ce que cela révèle sur leur stratégie",
  "impact_pour_nous": "comment cela nous affecte concrètement",
  "action_recommandee": "action concrète et actionnable",
  "urgence": "immediat|semaine|mois|aucune"
}}"""
    try:
        return appeler_gemini(prompt, temperature=0.3, max_tokens=700)
    except:
        return {"interpretation_changements": "Indisponible", "urgence": "aucune"}

# ──────────────────────────────────────────────
# OUTIL 6 : SYNTHÈSE GLOBALE
# ──────────────────────────────────────────────
def generer_synthese(toutes_analyses: list[dict], date_rapport: str) -> dict:
    """Génère la synthèse stratégique globale avec Gemini."""
    resume_analyses = [{
        "nom": a["nom"], "url": a["url"], "categorie": a.get("categorie",""),
        "title": a.get("title",""),
        "mots_cles": a.get("mots_cles_principaux", []),
        "intention": a.get("intention_contenu",""),
        "score_qualite": a.get("score_qualite", 5),
        "niveau_menace": a.get("niveau_menace","moyen"),
        "opportunites": a.get("opportunites", []),
        "comparaison": a.get("comparaison", {}),
    } for a in toutes_analyses]

    tous_mots = [m for a in toutes_analyses for m in (a.get("mots_cles_principaux") or [])]
    freq = {}
    for m in tous_mots:
        freq[m] = freq.get(m, 0) + 1
    n = len(toutes_analyses)
    mots_competitifs = [m for m, c in freq.items() if c >= n // 2]
    mots_opportunites = list({m for m, c in freq.items() if c == 1})[:25]

    alertes = [
        {"nom": a["nom"], "url": a["url"], "niveau": a["comparaison"]["niveau_changement"],
         "urgence": a.get("interpretation", {}).get("urgence", "aucune")}
        for a in toutes_analyses if a.get("comparaison", {}).get("alerte")
    ]

    prompt = f"""Tu es directeur stratégie SEO spécialisé en décoration marocaine et artisanat berbère.
Génère une synthèse stratégique pour Safia Rugs. Retourne UNIQUEMENT du JSON valide.

{n} concurrents analysés.
Analyses : {json.dumps(resume_analyses, ensure_ascii=False)}
Mots compétitifs : {', '.join(mots_competitifs)}
Opportunités mots-clés : {', '.join(mots_opportunites)}
Alertes : {json.dumps(alertes, ensure_ascii=False)}

JSON attendu :
{{
  "resume_executif": "synthèse décisionnelle en 3 phrases",
  "tendance_dominante": "tendance principale observée",
  "faiblesses_concurrents": {{"nom_concurrent": "faiblesse exploitable"}},
  "opportunites_non_exploitees": [
    {{"sujet": "sujet précis", "potentiel": "fort|moyen", "intention": "transactionnel|informationnel|mixte", "raison": "pourquoi c'est une opportunité"}}
  ],
  "recommandations_actionnables": [
    {{"action": "action précise", "priorite": "haute|moyenne|faible", "impact_estime": "fort|moyen|faible"}}
  ],
  "tendances_detectees": ["tendance 1", "tendance 2"],
  "alerte_strategique": "alerte principale ou Aucune alerte majeure",
  "score_menace_global": 6
}}"""
    try:
        synthese = appeler_gemini(prompt, temperature=0.4, max_tokens=2500)
    except Exception as e:
        print(f"[GEMINI] Erreur synthèse: {e}")
        synthese = {
            "resume_executif": "Synthèse indisponible", "tendance_dominante": "",
            "faiblesses_concurrents": {}, "opportunites_non_exploitees": [],
            "recommandations_actionnables": [], "tendances_detectees": [],
            "alerte_strategique": "Aucune", "score_menace_global": 5
        }

    return {
        "synthese": synthese,
        "toutes_analyses": toutes_analyses,
        "resume_analyses": resume_analyses,
        "mots_competitifs": mots_competitifs,
        "mots_opportunites": mots_opportunites,
        "alertes": alertes,
        "nb_concurrents": n,
        "nb_alertes": len(alertes),
        "semaine_iso": semaine_iso(),
        "date_rapport": date_rapport
    }

# ──────────────────────────────────────────────
# OUTIL 7 : SCORING OPPORTUNITÉS
# ──────────────────────────────────────────────
def scorer_opportunites(donnees: dict) -> dict:
    """Score et classe les opportunités SEO."""
    synthese = donnees["synthese"]
    mots_competitifs = donnees.get("mots_competitifs", [])
    opps = synthese.get("opportunites_non_exploitees", [])

    def score(opp):
        pot    = 8 if opp.get("potentiel") == "fort" else 5
        intent = {"transactionnel": 10, "transactionnelle": 10, "commercial": 8,
                  "commerciale": 8, "mixte": 6, "informationnel": 4, "informationnelle": 4
                  }.get((opp.get("intention") or "").lower(), 5)
        comp   = 3 if any(m.lower() in (opp.get("sujet") or "").lower() for m in mots_competitifs) else 9
        s      = round(pot * 0.35 + intent * 0.35 + comp * 0.30, 1)
        return {**opp, "score_final": s,
                "priorite": "CRITIQUE" if s >= 8 else "HAUTE" if s >= 6.5 else "MOYENNE" if s >= 5 else "FAIBLE"}

    scorees = sorted([score(o) for o in opps], key=lambda x: x["score_final"], reverse=True)
    top_3   = scorees[:3]

    return {
        **donnees,
        "opportunites_scorees": scorees,
        "top_3": top_3,
        "nb_opportunites": len(scorees),
        "nb_critiques": sum(1 for o in scorees if o["priorite"] == "CRITIQUE"),
        "score_menace": synthese.get("score_menace_global", 5)
    }

# ──────────────────────────────────────────────
# OUTIL 8 : FICHES D'ACTION
# ──────────────────────────────────────────────
def generer_fiches_action(scoring: dict) -> list[dict]:
    """Génère les fiches d'action détaillées pour le TOP 3."""
    top_3 = scoring.get("top_3", [])
    if not top_3:
        return []

    prompt = f"""Tu es consultant SEO senior spécialisé artisanat marocain et décoration berbère.
Génère des fiches d'action pour le TOP 3 des opportunités de Safia Rugs (e-commerce Shopify, tapis berbères, poufs, décoration marocaine, ciblant France et Maroc).
Retourne UNIQUEMENT du JSON valide.

Top 3 opportunités : {json.dumps(top_3, ensure_ascii=False)}

JSON attendu :
{{
  "fiches_action": [
    {{
      "sujet": "sujet précis",
      "score": 7.8,
      "priorite": "CRITIQUE|HAUTE|MOYENNE",
      "type_contenu_recommande": "article de blog|landing page|guide|comparatif|FAQ|page collection",
      "titre_suggere": "Titre SEO optimisé prêt à utiliser",
      "meta_description_suggeree": "Meta description prête à copier (max 155 car)",
      "structure_suggeree": ["H2 : Section 1","H2 : Section 2","H2 : Section 3"],
      "mots_cles_a_cibler": ["mot-clé 1","mot-clé 2","mot-clé 3"],
      "mots_cles_longue_traine": ["expression 1","expression 2"],
      "angle_differentiant": "comment Safia Rugs se différencie",
      "effort_estime": "demi-journée|1 jour|2-3 jours",
      "impact_estime": "fort|moyen",
      "url_suggeree": "/blogs/conseils-de-safae/slug-url"
    }}
  ]
}}"""
    try:
        r = appeler_gemini(prompt, temperature=0.5, max_tokens=2000)
        return r.get("fiches_action", [])
    except:
        return []

# ──────────────────────────────────────────────
# OUTIL 9 : BUILDER RAPPORT HTML
# ──────────────────────────────────────────────
def builder_rapport_html(scoring: dict, fiches: list[dict]) -> str:
    """Génère le rapport HTML complet."""
    donnees  = scoring
    synthese = scoring.get("synthese", {})
    opps     = scoring.get("opportunites_scorees", [])
    alertes  = scoring.get("alertes", [])
    score_m  = scoring.get("score_menace", 5)
    sem      = scoring.get("semaine_iso", "")
    date_r   = scoring.get("date_rapport", "")
    nb_c     = scoring.get("nb_concurrents", 0)

    couleur_m = "#dc3545" if score_m >= 8 else "#fd7e14" if score_m >= 6 else "#28a745"
    label_m   = "CRITIQUE" if score_m >= 8 else "ÉLEVÉE" if score_m >= 6 else "MODÉRÉE"

    def badge(p):
        styles = {"CRITIQUE":"background:#dc3545;color:white","HAUTE":"background:#fd7e14;color:white",
                  "MOYENNE":"background:#ffc107;color:#333","FAIBLE":"background:#6c757d;color:white"}
        s = styles.get(p, styles["FAIBLE"])
        return f'<span style="{s};padding:2px 9px;border-radius:12px;font-size:11px;font-weight:700">{p}</span>'

    def badge_urgence(u):
        styles = {"immediat":"background:#dc3545;color:white","semaine":"background:#fd7e14;color:white",
                  "mois":"background:#ffc107;color:#333","aucune":"background:#6c757d;color:white"}
        labels = {"immediat":"🔴 Immédiat","semaine":"🟠 Cette semaine","mois":"🟡 Ce mois","aucune":"⚪ Aucune"}
        style = styles.get(u, styles["aucune"])
        label = labels.get(u, u)
        return f'<span style="{style};padding:2px 9px;border-radius:12px;font-size:11px;font-weight:700">{label}</span>'

    rows_opps = "".join([
        f'<tr><td><strong>#{i+1}</strong> {o.get("sujet","—")}</td>'
        f'<td style="text-align:center"><strong>{o.get("score_final","")}/10</strong></td>'
        f'<td style="text-align:center">{badge(o.get("priorite","FAIBLE"))}</td>'
        f'<td style="text-align:center">{o.get("potentiel","—")}</td>'
        f'<td style="font-size:11px;color:#666">{o.get("raison","—")}</td></tr>'
        for i, o in enumerate(opps[:10])
    ])

    rows_alertes = "".join([
        f'<div style="background:#fff3cd;border-left:4px solid #ffc107;padding:10px 14px;margin:8px 0;border-radius:4px">'
        f'<strong>⚠️ {a["nom"]}</strong> — Changement {a["niveau"]} — Urgence : {badge_urgence(a.get("urgence","aucune"))}</div>'
        for a in alertes
    ]) or '<div style="background:#d4edda;border-left:4px solid #28a745;padding:10px 14px;border-radius:4px">✅ Aucun changement majeur cette semaine.</div>'

    html_fiches = "".join([
        f'''<div style="border:1px solid #e0e0e0;border-radius:8px;padding:20px;margin:16px 0;border-top:4px solid #0F6E56">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
          <h3 style="color:#0F6E56;margin:0;font-size:16px">#{i+1} — {f.get("sujet","")}</h3>
          <div>{badge(f.get("priorite","HAUTE"))} &nbsp; Score : <strong>{f.get("score","")}/10</strong></div>
        </div>
        <table style="width:100%;margin:12px 0;border-collapse:collapse;font-size:13px">
          <tr><td style="padding:4px 0;color:#666;width:140px"><strong>Type</strong></td><td>{f.get("type_contenu_recommande","—")}</td></tr>
          <tr><td style="padding:4px 0;color:#666"><strong>Titre suggéré</strong></td><td><em>{f.get("titre_suggere","—")}</em></td></tr>
          <tr><td style="padding:4px 0;color:#666"><strong>URL suggérée</strong></td><td><code style="font-size:11px;background:#f5f5f5;padding:2px 6px;border-radius:3px">{f.get("url_suggeree","—")}</code></td></tr>
          <tr><td style="padding:4px 0;color:#666"><strong>Effort</strong></td><td>{f.get("effort_estime","—")} | Impact : {f.get("impact_estime","—")}</td></tr>
        </table>
        <div style="background:#f8f9fa;padding:10px 14px;border-radius:4px;margin:8px 0">
          <strong>Meta description :</strong><br><span style="font-size:12px;color:#555">{f.get("meta_description_suggeree","—")}</span>
        </div>
        <div style="margin:10px 0">
          <strong>Mots-clés :</strong> {''.join(f'<span style="background:#e8f4f8;color:#1B3A6B;padding:2px 8px;border-radius:10px;font-size:11px;margin:2px;display:inline-block">{m}</span>' for m in f.get("mots_cles_a_cibler",[]))}
        </div>
        <div style="margin:10px 0">
          <strong>Structure :</strong>
          <ul style="margin:6px 0;padding-left:18px;font-size:13px">{''.join(f"<li>{s}</li>" for s in f.get("structure_suggeree",[]))}</ul>
        </div>
        <div style="background:#e8f4ee;padding:10px 14px;border-radius:4px;border-left:3px solid #0F6E56">
          <strong>💡 Angle différenciant :</strong> {f.get("angle_differentiant","—")}
        </div></div>'''
        for i, f in enumerate(fiches)
    ])

    recos = "".join([
        f'<tr><td><strong>#{i+1}</strong> {r.get("action","")}</td>'
        f'<td style="text-align:center">{badge(r.get("priorite","MOYENNE").upper())}</td>'
        f'<td style="text-align:center">{r.get("impact_estime","—")}</td></tr>'
        for i, r in enumerate(synthese.get("recommandations_actionnables",[]))
    ])

    tendances = "".join([f"<li>{t}</li>" for t in synthese.get("tendances_detectees",[])])

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rapport SEO {sem} — Safia Rugs</title>
<style>
* {{ box-sizing:border-box;margin:0;padding:0 }}
body {{ font-family:'Segoe UI',Arial,sans-serif;background:#f0f2f5;color:#1B3A6B;font-size:14px }}
.wrapper {{ max-width:680px;margin:0 auto;background:white }}
.header {{ background:linear-gradient(135deg,#1B3A6B 0%,#0F6E56 100%);color:white;padding:32px 28px }}
.header h1 {{ font-size:22px;font-weight:700;margin-bottom:6px }}
.header p {{ font-size:13px;opacity:0.85 }}
.content {{ padding:28px }}
.section-title {{ font-size:16px;font-weight:700;color:#1B3A6B;border-left:4px solid #0F6E56;padding-left:12px;margin:28px 0 14px }}
.kpi-grid {{ display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0 }}
.kpi {{ background:#e8f4ee;padding:14px;border-radius:8px;text-align:center }}
.kpi-val {{ font-size:26px;font-weight:700;color:#0F6E56 }}
.kpi-lab {{ font-size:11px;color:#666;margin-top:4px }}
.resume-box {{ background:#e8f4ee;border-left:4px solid #0F6E56;padding:14px 16px;border-radius:4px;margin:12px 0;line-height:1.6 }}
table {{ width:100%;border-collapse:collapse;margin:12px 0;font-size:13px }}
th {{ background:#1B3A6B;color:white;padding:9px 12px;text-align:left;font-size:12px }}
td {{ padding:9px 12px;border-bottom:1px solid #eee;vertical-align:top }}
tr:nth-child(even) td {{ background:#f9f9f9 }}
.footer {{ background:#1B3A6B;color:white;padding:20px 28px;text-align:center;font-size:11px;margin-top:28px }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>📊 Rapport SEO — Intelligence Concurrentielle</h1>
    <p>Safia Rugs &nbsp;·&nbsp; {sem} &nbsp;·&nbsp; {date_r}</p>
  </div>
  <div class="content">
    <div class="kpi-grid">
      <div class="kpi"><div class="kpi-val">{nb_c}</div><div class="kpi-lab">Concurrents</div></div>
      <div class="kpi"><div class="kpi-val">{scoring.get("nb_opportunites",0)}</div><div class="kpi-lab">Opportunités</div></div>
      <div class="kpi"><div class="kpi-val">{scoring.get("nb_critiques",0)}</div><div class="kpi-lab">Critiques</div></div>
      <div class="kpi"><div class="kpi-val" style="color:{couleur_m}">{score_m}/10</div><div class="kpi-lab">Menace {label_m}</div></div>
    </div>

    <div class="section-title">🎯 Résumé Exécutif</div>
    <div class="resume-box">{synthese.get("resume_executif","—")}</div>
    <div style="background:#f8f9fa;padding:10px 14px;border-radius:4px;margin:8px 0">
      <strong>Tendance dominante :</strong> {synthese.get("tendance_dominante","—")}
    </div>
    <div style="background:#f8f9fa;padding:10px 14px;border-radius:4px;margin:8px 0">
      <strong style="color:{couleur_m}">⚠️ Alerte stratégique :</strong> {synthese.get("alerte_strategique","Aucune")}
    </div>

    <div class="section-title">🔔 Changements Concurrents</div>
    {rows_alertes}

    <div class="section-title">🏆 Top Opportunités SEO</div>
    <table>
      <tr><th>Opportunité</th><th>Score</th><th>Priorité</th><th>Potentiel</th><th>Raison</th></tr>
      {rows_opps}
    </table>

    <div class="section-title">📋 Plans d'Action — Top 3</div>
    {html_fiches}

    <div class="section-title">✅ Recommandations</div>
    <table>
      <tr><th>Action</th><th>Priorité</th><th>Impact</th></tr>
      {recos}
    </table>

    {"<div class='section-title'>📈 Tendances Détectées</div><ul style='padding-left:20px;line-height:1.8'>" + tendances + "</ul>" if tendances else ""}
  </div>
  <div class="footer">
    AI SEO Competitive Intelligence &nbsp;·&nbsp; Safia Rugs &nbsp;·&nbsp; {date_r}<br>
    <span style="opacity:0.7">Généré automatiquement · Agent IA Python + Gemini 2.0 Flash</span>
  </div>
</div>
</body>
</html>"""

# ──────────────────────────────────────────────
# OUTIL 10 : ENVOYER EMAIL
# ──────────────────────────────────────────────
def envoyer_email(destinataire: str, sujet: str, html: str):
    """Envoie le rapport HTML par email via Gmail SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = sujet
        msg["From"]    = GMAIL_USER
        msg["To"]      = destinataire
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(GMAIL_USER, GMAIL_PASSWORD)
            srv.sendmail(GMAIL_USER, destinataire, msg.as_string())
        print(f"[EMAIL] Rapport envoyé à {destinataire}")
    except Exception as e:
        print(f"[EMAIL] Erreur envoi: {e}")
        # Sauvegarde locale si email échoue
        path = f"rapport_{semaine_iso()}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[EMAIL] Rapport sauvegardé localement: {path}")

# ──────────────────────────────────────────────
# OUTIL 11 : SUGGESTIONS SUJETS BLOG
# ──────────────────────────────────────────────
def suggerer_sujets_blog(analyses: list = None, nb: int = 10) -> list:
    """Génère des suggestions de sujets blog basées sur l'analyse concurrentielle et la stratégie SEO."""
    ctx = SAFIA_CONTEXT

    opportunites_str = ""
    if analyses:
        mots = [m for a in analyses for m in (a.get("mots_cles_principaux") or [])]
        opps = [o for a in analyses for o in (a.get("opportunites") or [])]
        freq = {}
        for m in mots:
            freq[m] = freq.get(m, 0) + 1
        mots_gap = [m for m, c in freq.items() if c == 1][:15]
        opportunites_str = f"\nMots-clés non exploités par les concurrents : {', '.join(mots_gap)}\nOpportunités détectées : {'; '.join(opps[:10])}"

    prompt = f"""Tu es expert SEO et content marketing spécialisé en artisanat marocain et décoration berbère.
Génère exactement {nb} idées d'articles de blog percutantes pour {ctx['marque']}.
Boutique : {ctx['boutique']}
Marché : {', '.join(ctx['marches'])}
Audience : {ctx['audience']}
Catégories produits : {', '.join(ctx['categories'])}
Mots-clés prioritaires : {', '.join(ctx['mots_cles_p1'] + ctx['mots_cles_p2'])}
Articles déjà publiés (ne pas dupliquer) : {'; '.join(ctx['articles_blog_existants'])}
{opportunites_str}

Varie les types : guides, comparatifs, listes inspiration, tutoriels déco, FAQ, interviews artisans, histoires produits.
Retourne UNIQUEMENT du JSON valide.

JSON attendu :
{{
  "sujets": [
    {{
      "titre": "Titre SEO optimisé prêt à publier (55-65 caractères)",
      "slug_url": "slug-url-en-minuscules-sans-accents",
      "mots_cles_cibles": ["mot-clé 1", "mot-clé 2", "mot-clé 3"],
      "volume_mensuel_estime": "800",
      "intention": "informationnelle|commerciale|transactionnelle|mixte",
      "type_contenu": "guide|comparatif|liste|tutoriel|inspiration|FAQ|storytelling",
      "priorite": "P1|P2|P3",
      "pourquoi": "raison SEO et business en 1 phrase",
      "effort_redaction": "demi-journée|1 jour|2 jours",
      "potentiel_conversion": "fort|moyen|faible"
    }}
  ]
}}"""
    try:
        r = appeler_gemini(prompt, temperature=0.65, max_tokens=3000)
        return r.get("sujets", [])
    except Exception as e:
        print(f"[BLOG] Erreur suggestions sujets: {e}")
        return []


# ──────────────────────────────────────────────
# OUTIL 12 : BRIEF SEO COMPLET
# ──────────────────────────────────────────────
def generer_brief_seo(sujet: str, mots_cles: list = None) -> dict:
    """Génère un brief SEO complet et actionnable pour un article Safia Rugs."""
    ctx = SAFIA_CONTEXT
    mots_str = ", ".join(mots_cles) if mots_cles else "à déterminer selon le sujet"

    prompt = f"""Tu es content strategist SEO senior spécialisé en e-commerce artisanat marocain.
Génère un brief SEO complet pour {ctx['marque']} ({ctx['boutique']}).
Audience : {ctx['audience']}
Ton éditorial : {ctx['ton']}
Blog : {ctx['blog_url']}

Sujet demandé : {sujet}
Mots-clés fournis : {mots_str}

Retourne UNIQUEMENT du JSON valide.

JSON attendu :
{{
  "titre_seo": "Titre balise <title> optimisé (50-60 caractères)",
  "titre_h1": "H1 humain et engageant (différent du title, peut être plus long)",
  "meta_description": "Meta description 148-155 caractères avec verbe d'action et mot-clé principal",
  "url_slug": "slug-url-optimise-sans-accents",
  "mots_cles_principaux": ["mc1", "mc2", "mc3"],
  "mots_cles_secondaires": ["mc4", "mc5", "mc6", "mc7"],
  "mots_cles_longue_traine": ["expression longue 1", "expression longue 2", "expression longue 3"],
  "intention_recherche": "informationnelle|commerciale|transactionnelle|mixte",
  "type_contenu": "guide|comparatif|liste|tutoriel|inspiration|FAQ|storytelling",
  "longueur_cible_mots": 1600,
  "structure": [
    {{
      "niveau": "H2",
      "titre": "Titre de la section H2",
      "contenu_attendu": "Ce que cette section doit couvrir en 1-2 phrases",
      "mots_cles_a_inclure": ["mc à placer ici"]
    }}
  ],
  "angle_differentiant": "Ce qui rend cet article unique vs concurrents comme Tribaliste, Tamazi, Mazir ou Secret Berbère",
  "cta_recommandes": ["CTA 1 vers une collection", "CTA 2 en milieu d'article"],
  "liens_internes": ["URL ou slug de page à lier", "autre page interne"],
  "medias_recommandes": "Description des visuels, photos produits et infographies à ajouter",
  "faq_schema": [
    {{"question": "Question fréquente 1 ?", "reponse_courte": "Réponse directe en 1-2 phrases"}},
    {{"question": "Question fréquente 2 ?", "reponse_courte": "Réponse directe"}},
    {{"question": "Question fréquente 3 ?", "reponse_courte": "Réponse directe"}}
  ],
  "temps_lecture_estime": "7 min",
  "notes_redacteur": "Conseils spécifiques pour le rédacteur sur le ton, les anecdotes à inclure, les produits à mentionner"
}}"""
    try:
        return appeler_gemini(prompt, temperature=0.3, max_tokens=3000)
    except Exception as e:
        print(f"[BLOG] Erreur brief SEO: {e}")
        return {}


# ──────────────────────────────────────────────
# OUTIL 13 : ARTICLE COMPLET RÉDIGÉ
# ──────────────────────────────────────────────
def generer_article_complet(brief: dict) -> str:
    """Rédige l'article de blog complet en Markdown, prêt à publier sur Shopify."""
    ctx = SAFIA_CONTEXT

    structure_str = "\n".join([
        f"  {s.get('niveau','H2')}: {s.get('titre','')} — {s.get('contenu_attendu','')}"
        for s in brief.get("structure", [])
    ])
    faq_str = "\n".join([
        f"  Q: {f.get('question','')} → R: {f.get('reponse_courte','')}"
        for f in brief.get("faq_schema", [])
    ])

    prompt = f"""Tu es rédacteur SEO expert en artisanat marocain et décoration berbère pour {ctx['marque']}.
Rédige un article de blog COMPLET, engageant et optimisé SEO.

CONTEXTE MARQUE :
- Boutique : {ctx['boutique']}
- USP : {ctx['usp']}
- Audience : {ctx['audience']}
- Ton : {ctx['ton']}
- Blog : {ctx['blog_url']}

BRIEF ARTICLE :
- Titre H1 : {brief.get('titre_h1', brief.get('titre_seo', ''))}
- URL : {ctx['blog_slug_prefix']}{brief.get('url_slug', '')}
- Mots-clés principaux : {', '.join(brief.get('mots_cles_principaux', []))}
- Mots-clés secondaires : {', '.join(brief.get('mots_cles_secondaires', []))}
- Longue traîne : {', '.join(brief.get('mots_cles_longue_traine', []))}
- Longueur cible : {brief.get('longueur_cible_mots', 1600)} mots
- Angle différenciant : {brief.get('angle_differentiant', '')}
- CTAs : {', '.join(brief.get('cta_recommandes', []))}
- Liens internes : {', '.join(brief.get('liens_internes', []))}

STRUCTURE À RESPECTER :
{structure_str}

FAQ À INCLURE EN FIN D'ARTICLE :
{faq_str}

INSTRUCTIONS DE RÉDACTION :
1. Commence par une introduction accrocheuse (2-3 paragraphes) qui pose le problème et capte l'attention
2. Utilise les mots-clés naturellement — pas de répétition forcée
3. Valorise les artisans berbères et le savoir-faire marocain avec des anecdotes concrètes
4. Chaque section H2 doit apporter une vraie valeur ajoutée (pas de remplissage)
5. Insère les CTAs vers la boutique à des moments naturels (jamais intrusifs)
6. Termine par un paragraphe de conclusion + appel à l'action vers safia-rugs.com
7. Format : Markdown propre — ## pour H2, ### pour H3, **gras** pour les points clés
8. Longueur : {brief.get('longueur_cible_mots', 1600)} mots minimum

Rédige l'article complet maintenant (en français) :"""

    try:
        return appeler_gemini_texte(prompt, temperature=0.62, max_tokens=4096)
    except Exception as e:
        print(f"[BLOG] Erreur génération article: {e}")
        return "Erreur lors de la génération de l'article. Vérifiez votre clé Gemini."


# ──────────────────────────────────────────────
# OUTIL 14 : ANALYSER MON SITE (safia-rugs.com vs concurrents)
# ──────────────────────────────────────────────
def analyser_mon_site(analyses_concurrents: list = None) -> dict:
    """Scrape et analyse safia-rugs.com, puis le compare aux concurrents."""
    ctx = SAFIA_CONTEXT
    url_safia = ctx["url"]

    print(f"[MON SITE] Scraping {url_safia}...")
    html = scraper_page(url_safia)
    page_data = parser_html(html, {"nom": "Safia Rugs", "url": url_safia, "categorie": "e-commerce"})

    # Analyse IA spécifique Safia
    resume_concurrents = ""
    if analyses_concurrents:
        resume_concurrents = json.dumps([{
            "nom": a.get("nom"), "title": a.get("title"),
            "mots_cles": a.get("mots_cles_principaux", []),
            "score": a.get("score_qualite", 5),
            "points_forts": a.get("points_forts", []),
        } for a in analyses_concurrents[:5]], ensure_ascii=False)

    prompt = f"""Tu es consultant SEO senior. Analyse le site {ctx['marque']} ({url_safia}) et compare-le à ses concurrents.
Retourne UNIQUEMENT du JSON valide.

DONNÉES DU SITE SAFIA RUGS :
Title : {page_data.get('title','')}
H1 : {page_data.get('h1','')}
H2s : {page_data.get('h2s','')}
Meta desc : {page_data.get('meta_desc','')}
Schema.org : {page_data.get('a_schema',False)}
Canonical : {page_data.get('a_canonical',False)}
Nb liens : {page_data.get('nb_liens',0)}
Taille : {page_data.get('taille_page_kb',0)}kb
Contenu : {page_data.get('texte_brut','')[:2000]}

DONNÉES CONCURRENTS (pour comparaison) :
{resume_concurrents or "Pas encore analysés"}

JSON attendu :
{{
  "score_seo_global": 7,
  "score_technique": 6,
  "score_contenu": 7,
  "points_forts": ["force 1", "force 2", "force 3"],
  "points_faibles": ["faiblesse 1", "faiblesse 2", "faiblesse 3"],
  "vs_concurrents": "comment Safia se positionne vs ses concurrents en 2 phrases",
  "mots_cles_presents": ["mc1", "mc2", "mc3"],
  "mots_cles_manquants": ["mc manquant 1", "mc manquant 2", "mc manquant 3"],
  "quick_wins": [
    {{"action": "action précise et actionnable", "impact": "fort|moyen", "effort": "faible|moyen|élevé", "delai": "aujourd'hui|cette semaine|ce mois"}}
  ],
  "optimisations_prioritaires": [
    {{"page": "URL ou nom de page", "probleme": "description du problème", "solution": "solution concrète"}}
  ],
  "alerte_critique": "problème SEO critique à corriger en urgence ou Aucune alerte critique"
}}"""

    try:
        analyse_ia = appeler_gemini(prompt, temperature=0.2, max_tokens=2500)
    except Exception as e:
        print(f"[MON SITE] Erreur analyse IA: {e}")
        analyse_ia = {"score_seo_global": 5, "points_forts": [], "points_faibles": [],
                      "quick_wins": [], "optimisations_prioritaires": [], "alerte_critique": "Analyse indisponible"}

    return {**page_data, **analyse_ia, "date_analyse": datetime.now().strftime("%d/%m/%Y %H:%M")}


# ──────────────────────────────────────────────
# OUTIL 15 : CALENDRIER DE CONTENU
# ──────────────────────────────────────────────
def generer_calendrier_contenu(nb_semaines: int = 4, analyses: list = None) -> list:
    """Génère un calendrier de contenu blog sur N semaines."""
    ctx = SAFIA_CONTEXT
    from datetime import timedelta

    opportunites_str = ""
    if analyses:
        opps = [o for a in analyses for o in (a.get("opportunites") or [])]
        mots_gap = list({m for a in analyses for m in (a.get("mots_cles_principaux") or [])})[:15]
        opportunites_str = f"Opportunités concurrentielles : {'; '.join(opps[:8])}\nMots-clés gaps : {', '.join(mots_gap)}"

    # Calculer les dates de publication (lundis)
    today = date.today()
    lundis = []
    d = today
    while len(lundis) < nb_semaines:
        if d.weekday() == 0:
            lundis.append(d)
        d += timedelta(days=1)

    prompt = f"""Tu es content strategist SEO pour {ctx['marque']} ({ctx['url']}).
Blog : "{ctx['blog_nom']}" — ton : {ctx['ton']}
Audience : {ctx['audience']}
Collections : {', '.join(ctx['navigation'][:5])}
Mots-clés P1 : {', '.join(ctx['mots_cles_p1'])}
Articles existants : {'; '.join(ctx['articles_blog_existants'])}
{opportunites_str}

Génère un calendrier de contenu pour {nb_semaines} semaines.
Équilibre : 40% guides/informationnels, 30% inspiration/déco, 20% produits/collections, 10% storytelling marque.
Retourne UNIQUEMENT du JSON valide.

JSON attendu :
{{
  "calendrier": [
    {{
      "semaine": 1,
      "titre": "Titre SEO optimisé (55-65 car.)",
      "slug_url": "slug-url",
      "type": "guide|inspiration|produit|storytelling|FAQ|comparatif",
      "mots_cles": ["mc1", "mc2", "mc3"],
      "volume_estime": "600",
      "intention": "informationnelle|commerciale|mixte",
      "angle": "angle unique en 1 phrase",
      "cta_principal": "vers quelle collection/page rediriger",
      "priorite": "haute|moyenne",
      "effort": "demi-journée|1 jour|2 jours"
    }}
  ]
}}"""

    try:
        r = appeler_gemini(prompt, temperature=0.6, max_tokens=3000)
        calendrier = r.get("calendrier", [])
        for i, item in enumerate(calendrier):
            if i < len(lundis):
                item["date_publication"] = lundis[i].strftime("%d/%m/%Y")
                item["semaine_iso"] = f"{lundis[i].year}-S{lundis[i].isocalendar()[1]:02d}"
        return calendrier
    except Exception as e:
        print(f"[CALENDRIER] Erreur: {e}")
        return []


# ──────────────────────────────────────────────
# VÉRIFICATION ANALYSE BIMENSUELLE
# ──────────────────────────────────────────────
def verifier_analyse_due() -> tuple[bool, str]:
    """Retourne (True, message) si une analyse est due (toutes les 2 semaines)."""
    try:
        gc = get_sheets_client()
        sh = gc.open_by_key(SHEETS_ID)
        ws = sh.worksheet("rapports_hebdo")
        rows = ws.get_all_records()
        if not rows:
            return True, "Aucune analyse précédente — première analyse"
        derniere = rows[-1]
        sem_str = str(derniere.get("semaine_iso") or derniere.get("Semaine ISO\n(ex: 2025-S02)", ""))
        if not sem_str or "-S" not in sem_str:
            return False, "Impossible de lire la date"
        annee_dern, sem_dern = int(sem_str.split("-S")[0]), int(sem_str.split("-S")[1])
        today = date.today()
        diff = (today.year * 52 + today.isocalendar()[1]) - (annee_dern * 52 + sem_dern)
        if diff >= 2:
            return True, f"Dernière analyse : {sem_str} — {diff} sem. de retard"
        return False, f"Prochaine analyse dans {(2 - diff) * 7} jours"
    except Exception as e:
        return False, f"Vérification impossible : {e}"


# ──────────────────────────────────────────────
# GESTION MOT DE PASSE — persistance cloud via Sheets
# ──────────────────────────────────────────────
def lire_password_config() -> Optional[str]:
    """Lit le mot de passe depuis l'onglet 'config' du Google Sheet.
    Retourne None si absent (fallback sur la variable d'environnement)."""
    try:
        gc = get_sheets_client()
        sh = gc.open_by_key(SHEETS_ID)
        try:
            ws = sh.worksheet("config")
        except Exception:
            return None
        for row in ws.get_all_records():
            if row.get("cle") == "DASHBOARD_PASSWORD":
                v = str(row.get("valeur", "")).strip()
                return v if v else None
        return None
    except Exception:
        return None

def ecrire_password_config(new_pass: str) -> bool:
    """Écrit le nouveau mot de passe dans l'onglet 'config' du Google Sheet.
    Crée l'onglet automatiquement s'il n'existe pas encore."""
    try:
        gc = get_sheets_client()
        sh = gc.open_by_key(SHEETS_ID)
        try:
            ws = sh.worksheet("config")
        except Exception:
            ws = sh.add_worksheet(title="config", rows=20, cols=3)
            ws.append_row(["cle", "valeur", "description"])
        rows = ws.get_all_records()
        for i, row in enumerate(rows, start=2):
            if row.get("cle") == "DASHBOARD_PASSWORD":
                ws.update_cell(i, 2, new_pass)
                return True
        ws.append_row(["DASHBOARD_PASSWORD", new_pass, "Mot de passe du dashboard"])
        return True
    except Exception as e:
        print(f"[SHEETS] Erreur écriture password: {e}")
        return False


# ──────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ──────────────────────────────────────────────
def run_analyse_complete(destinataire: str = None) -> dict:
    """
    Lance l'analyse complète de tous les concurrents.
    Retourne le résultat complet (html, stats, opportunités).
    """
    print("=" * 60)
    print(f"[AGENT SEO] Démarrage analyse — {semaine_iso()}")
    print("=" * 60)

    date_rapport = datetime.now().strftime("%A %d %B %Y")

    # 1. Lire les concurrents
    concurrents = lire_concurrents()
    if not concurrents:
        return {"erreur": "Aucun concurrent trouvé dans Google Sheets"}
    print(f"[1/8] {len(concurrents)} concurrents actifs trouvés")

    # 2. Lire l'historique
    historique = lire_snapshots_historique()
    print(f"[2/8] {len(historique)} snapshots historiques chargés")

    # 3. Scraper + analyser chaque concurrent
    toutes_analyses = []
    for i, concurrent in enumerate(concurrents):
        print(f"[3/8] Scraping {i+1}/{len(concurrents)}: {concurrent['nom']}")

        html = scraper_page(concurrent["url"])
        page_data = parser_html(html, concurrent)
        analyse_ia = analyser_page_ia(page_data)

        analyse = {
            **page_data,
            "mots_cles_principaux":  analyse_ia.get("mots_cles_principaux", []),
            "mots_cles_secondaires": analyse_ia.get("mots_cles_secondaires", []),
            "mots_cles_longue_traine": analyse_ia.get("mots_cles_longue_traine", []),
            "intention_contenu":     analyse_ia.get("intention_contenu", "mixte"),
            "angle_editorial":       analyse_ia.get("angle_editorial", ""),
            "strategie_seo":         analyse_ia.get("strategie_seo_probable", ""),
            "resume_page":           analyse_ia.get("resume_page", ""),
            "score_qualite":         int(analyse_ia.get("score_qualite_contenu", 5)),
            "score_technique":       int(analyse_ia.get("score_technique_seo", 5)),
            "points_forts":          analyse_ia.get("points_forts_seo", []),
            "points_faibles":        analyse_ia.get("points_faibles_seo", []),
            "opportunites":          analyse_ia.get("opportunites_detectees", []),
            "audience_cible":        analyse_ia.get("type_audience_cible", ""),
            "ton_editorial":         analyse_ia.get("ton_editorial", ""),
            "niveau_menace":         analyse_ia.get("niveau_menace_concurrentielle", "moyen"),
        }

        # 4. Écrire snapshot
        ecrire_snapshot(analyse)

        # 5. Diff N vs N-1
        analyse["comparaison"] = calculer_diff(analyse, historique)

        # 6. Interpréter changements
        analyse["interpretation"] = interpreter_changements(analyse)

        toutes_analyses.append(analyse)
        print(f"    ✓ {concurrent['nom']} — score: {analyse['score_qualite']}/10 — menace: {analyse['niveau_menace']}")

    # 7. Synthèse globale + scoring
    print("[7/8] Génération synthèse globale...")
    donnees = generer_synthese(toutes_analyses, date_rapport)
    scoring = scorer_opportunites(donnees)

    # 8. Fiches d'action
    print("[8/8] Génération fiches d'action TOP 3...")
    fiches = generer_fiches_action(scoring)

    # Builder rapport HTML
    html_rapport = builder_rapport_html(scoring, fiches)

    # Envoyer email
    dest = destinataire or RAPPORT_DESTINATAIRE
    sem  = semaine_iso()
    sujet = f"📊 Rapport SEO Safia Rugs — {sem} | {scoring.get('nb_critiques',0)} opportunités critiques | Menace : {'ÉLEVÉE' if scoring.get('score_menace',5) >= 6 else 'MODÉRÉE'}"
    envoyer_email(dest, sujet, html_rapport)

    # Log rapport dans Sheets
    ecrire_log_rapport({
        "semaine_iso":     sem,
        "date_rapport":    date_rapport,
        "nb_concurrents":  scoring.get("nb_concurrents", 0),
        "nb_opportunites": scoring.get("nb_opportunites", 0),
        "nb_critiques":    scoring.get("nb_critiques", 0),
        "score_menace":    scoring.get("score_menace", 5),
    })

    print("=" * 60)
    print(f"[AGENT SEO] Analyse terminée — {scoring.get('nb_opportunites',0)} opportunités détectées")
    print("=" * 60)

    return {
        "statut": "success",
        "semaine_iso": sem,
        "nb_concurrents": scoring.get("nb_concurrents", 0),
        "nb_opportunites": scoring.get("nb_opportunites", 0),
        "nb_critiques": scoring.get("nb_critiques", 0),
        "score_menace": scoring.get("score_menace", 5),
        "top_3": scoring.get("top_3", []),
        "resume_executif": scoring.get("synthese", {}).get("resume_executif", ""),
        "alerte_strategique": scoring.get("synthese", {}).get("alerte_strategique", ""),
        "html_rapport": html_rapport,
        "toutes_analyses": toutes_analyses,
        "scoring": scoring,
        "fiches": fiches,
    }

# ──────────────────────────────────────────────
# INTERFACE CHAT AGENT
# ──────────────────────────────────────────────
class AgentSEOChat:
    """Agent conversationnel SEO + Blog — répond aux questions en langage naturel."""

    def __init__(self):
        self.historique: list[dict] = []
        self.dernier_rapport: Optional[dict] = None
        self.dernier_brief: Optional[dict] = None
        self.system_prompt = f"""Tu es l'agent IA de Safia Rugs, expert SEO et content marketing spécialisé en artisanat marocain et décoration berbère.
Boutique : {SAFIA_CONTEXT['boutique']} | Marchés : {', '.join(SAFIA_CONTEXT['marches'])}
Audience : {SAFIA_CONTEXT['audience']}
Catégories : {', '.join(SAFIA_CONTEXT['categories'])}
Mots-clés prioritaires : {', '.join(SAFIA_CONTEXT['mots_cles_p1'])}

Tu réponds en français, de manière concise et actionnable.
Tu peux aider sur : analyse concurrentielle SEO, stratégie de contenu, génération d'articles blog, optimisation on-page, mots-clés.
Tes recommandations sont toujours spécifiques à Safia Rugs avec des exemples concrets."""

    # ── Détection d'intention ──────────────────
    def _detecter_intention(self, message: str) -> str:
        m = message.lower()
        mots_blog = ["article", "blog", "rédige", "redige", "écris", "ecris",
                     "contenu", "sujet", "brief", "rédaction", "billet", "post"]
        mots_analyse = ["analys", "concurrent", "rapport", "semaine", "snapshot",
                        "scraping", "surveill", "menace"]
        mots_keywords = ["mot-clé", "mot clé", "keyword", "volume", "position",
                         "ranking", "longue traîne", "longue traine"]
        mots_suggestion = ["suggèr", "suggest", "idée", "idee", "liste", "propose",
                           "quoi écrire", "quoi rediger"]

        if any(k in m for k in mots_suggestion) and any(k in m for k in mots_blog):
            return "suggestion_blog"
        if any(k in m for k in ["brief", "plan d'article", "structure d'article"]):
            return "brief_blog"
        if any(k in m for k in ["rédige", "redige", "écris", "ecris", "génère un article", "genere un article", "article complet"]):
            return "article_complet"
        if any(k in m for k in mots_blog):
            return "blog_general"
        if any(k in m for k in mots_analyse):
            return "analyse_seo"
        if any(k in m for k in mots_keywords):
            return "keywords"
        return "general"

    def chat(self, message: str) -> str:
        """Traite un message et retourne une réponse — détecte automatiquement l'intention."""
        self.historique.append({"role": "user", "content": message})
        intention = self._detecter_intention(message)

        # ── Suggestions de sujets blog ──
        if intention == "suggestion_blog":
            analyses = self.dernier_rapport.get("toutes_analyses", []) if self.dernier_rapport else []
            sujets = suggerer_sujets_blog(analyses, nb=8)
            if sujets:
                lignes = [f"Voici **8 sujets d'articles** optimisés pour Safia Rugs :\n"]
                for i, s in enumerate(sujets, 1):
                    lignes.append(
                        f"**{i}. {s.get('titre','')}**\n"
                        f"   - Mots-clés : {', '.join(s.get('mots_cles_cibles',[]))}\n"
                        f"   - Volume : ~{s.get('volume_mensuel_estime','?')}/mois | Priorité : {s.get('priorite','')} | Potentiel conversion : {s.get('potentiel_conversion','')}\n"
                        f"   - Pourquoi : {s.get('pourquoi','')}\n"
                        f"   - Effort : {s.get('effort_redaction','')}\n"
                    )
                lignes.append("\n💡 Tapez **`/brief [numéro ou titre]`** pour générer le brief complet d'un article.")
                reponse = "\n".join(lignes)
            else:
                reponse = "Erreur lors de la génération des suggestions. Vérifiez votre clé Gemini."
            self.historique.append({"role": "assistant", "content": reponse})
            return reponse

        # ── Brief SEO ──
        if intention == "brief_blog":
            sujet = message
            for prefix in ["brief pour", "brief de", "brief sur", "génère un brief", "genere un brief", "donne-moi un brief"]:
                if prefix in message.lower():
                    sujet = message.lower().split(prefix, 1)[-1].strip()
                    break
            mots_cles = SAFIA_CONTEXT["mots_cles_p1"] + SAFIA_CONTEXT["mots_cles_p2"]
            brief = generer_brief_seo(sujet, mots_cles)
            self.dernier_brief = brief
            if brief:
                structure_str = "\n".join([f"   - {s.get('niveau','H2')}: {s.get('titre','')}" for s in brief.get("structure", [])])
                reponse = (
                    f"## Brief SEO — {brief.get('titre_h1', brief.get('titre_seo',''))}\n\n"
                    f"**Title SEO :** {brief.get('titre_seo','')}\n"
                    f"**H1 :** {brief.get('titre_h1','')}\n"
                    f"**Meta description :** {brief.get('meta_description','')}\n"
                    f"**URL :** `/blogs/conseils-de-safae/{brief.get('url_slug','')}`\n"
                    f"**Longueur cible :** {brief.get('longueur_cible_mots','')} mots | ⏱ {brief.get('temps_lecture_estime','')}\n\n"
                    f"**Mots-clés principaux :** {', '.join(brief.get('mots_cles_principaux',[]))}\n"
                    f"**Longue traîne :** {', '.join(brief.get('mots_cles_longue_traine',[]))}\n\n"
                    f"**Structure :**\n{structure_str}\n\n"
                    f"**Angle différenciant :** {brief.get('angle_differentiant','')}\n\n"
                    f"**Notes rédacteur :** {brief.get('notes_redacteur','')}\n\n"
                    f"💡 Tapez **`/article`** pour générer l'article complet basé sur ce brief."
                )
            else:
                reponse = "Impossible de générer le brief. Réessayez avec un sujet plus précis."
            self.historique.append({"role": "assistant", "content": reponse})
            return reponse

        # ── Article complet ──
        if intention == "article_complet":
            brief = self.dernier_brief
            if not brief:
                sujet = message
                for prefix in ["rédige un article sur", "redige un article sur", "écris un article sur",
                               "écris sur", "article sur", "article complet sur"]:
                    if prefix in message.lower():
                        sujet = message.lower().split(prefix, 1)[-1].strip()
                        break
                brief = generer_brief_seo(sujet, SAFIA_CONTEXT["mots_cles_p1"])
                self.dernier_brief = brief

            reponse = f"## ✍️ Article en cours de génération...\n\n"
            article = generer_article_complet(brief)
            reponse = f"---\n**Title :** {brief.get('titre_seo','')}\n**URL :** `/blogs/conseils-de-safae/{brief.get('url_slug','')}`\n\n---\n\n{article}"
            self.historique.append({"role": "assistant", "content": reponse})
            return reponse

        # ── Réponse générale avec contexte rapport ──
        contexte_rapport = ""
        if self.dernier_rapport:
            scoring = self.dernier_rapport.get("scoring", {})
            synthese = scoring.get("synthese", {})
            contexte_rapport = f"""
Données du dernier rapport SEO ({self.dernier_rapport.get('semaine_iso', '')}):
- Concurrents analysés: {self.dernier_rapport.get('nb_concurrents', 0)}
- Opportunités: {self.dernier_rapport.get('nb_opportunites', 0)} dont {self.dernier_rapport.get('nb_critiques', 0)} critiques
- Score menace: {self.dernier_rapport.get('score_menace', 5)}/10
- Résumé: {self.dernier_rapport.get('resume_executif', '')}
- Alerte: {self.dernier_rapport.get('alerte_strategique', '')}
- Top 3: {json.dumps(self.dernier_rapport.get('top_3', [])[:3], ensure_ascii=False)}
- Recommandations: {json.dumps(synthese.get('recommandations_actionnables', [])[:4], ensure_ascii=False)}
- Tendances: {', '.join(synthese.get('tendances_detectees', []))}
"""

        historique_str = "\n".join([
            f"{'Utilisateur' if h['role']=='user' else 'Assistant'}: {h['content'][:500]}"
            for h in self.historique[-6:]
        ])

        prompt = f"""{self.system_prompt}
{contexte_rapport}

Conversation récente:
{historique_str}

Réponds de manière utile, concise et actionnable en français.
Commandes disponibles : /analyser (analyse concurrents), /blog (suggestions articles), /brief [sujet], /article [sujet]."""

        reponse = appeler_gemini_texte(prompt, temperature=0.5, max_tokens=1500)
        self.historique.append({"role": "assistant", "content": reponse})
        return reponse

    def definir_rapport(self, rapport: dict):
        self.dernier_rapport = rapport


# ──────────────────────────────────────────────
# POINT D'ENTRÉE CLI
# ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "analyser":
        destinataire = sys.argv[2] if len(sys.argv) > 2 else None
        run_analyse_complete(destinataire)
    elif len(sys.argv) > 1 and sys.argv[1] == "blog":
        # python agent.py blog → suggestions de sujets
        print("Génération des suggestions de sujets blog...")
        sujets = suggerer_sujets_blog()
        for i, s in enumerate(sujets, 1):
            print(f"\n{i}. {s.get('titre','')} [{s.get('priorite','')}]")
            print(f"   Mots-clés: {', '.join(s.get('mots_cles_cibles',[]))}")
            print(f"   Volume: ~{s.get('volume_mensuel_estime','?')}/mois | {s.get('effort_redaction','')}")
    elif len(sys.argv) > 2 and sys.argv[1] == "brief":
        # python agent.py brief "sujet de l'article"
        sujet = " ".join(sys.argv[2:])
        print(f"Génération du brief SEO pour : {sujet}")
        brief = generer_brief_seo(sujet, SAFIA_CONTEXT["mots_cles_p1"])
        print(json.dumps(brief, ensure_ascii=False, indent=2))
    else:
        # Mode chat interactif
        print("=" * 60)
        print("  Agent SEO IA — Safia Rugs")
        print("  Commandes : /analyser | /blog | /brief [sujet] | /article [sujet]")
        print("  /quitter pour sortir")
        print("=" * 60)

        agent = AgentSEOChat()
        dernier_brief = None

        while True:
            msg = input("\nVous: ").strip()
            if not msg:
                continue
            if msg.lower() in ("/quitter", "/exit", "exit"):
                break
            elif msg.lower() in ("/analyser", "analyser"):
                print("\nAgent: Lancement de l'analyse complète...")
                rapport = run_analyse_complete()
                agent.definir_rapport(rapport)
                print(f"\nAgent: ✅ Analyse terminée ! {rapport.get('nb_opportunites',0)} opportunités — rapport email envoyé.")
            elif msg.lower() in ("/blog", "blog"):
                print("\nAgent: Génération des suggestions de sujets blog...")
                sujets = suggerer_sujets_blog(
                    agent.dernier_rapport.get("toutes_analyses", []) if agent.dernier_rapport else []
                )
                print(f"\nAgent: {agent.chat('suggère des sujets de blog')}")
            elif msg.lower().startswith("/brief "):
                sujet = msg[7:].strip()
                print(f"\nAgent: Génération du brief SEO pour '{sujet}'...")
                print(f"\nAgent: {agent.chat(f'brief pour {sujet}')}")
            elif msg.lower().startswith("/article "):
                sujet = msg[9:].strip()
                print(f"\nAgent: Génération de l'article complet sur '{sujet}'...")
                print(f"\nAgent: {agent.chat(f'rédige un article sur {sujet}')}")
            elif msg.lower() == "/article":
                print(f"\nAgent: {agent.chat('article complet')}")
            else:
                print(f"\nAgent: {agent.chat(msg)}")

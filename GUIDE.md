# 🚀 Guide de déploiement — Agent SEO IA Safia Rugs
## De n8n à un agent Python autonome en 30 minutes

---

## 📁 Structure des fichiers

```
agent_seo/
├── agent.py          # Logique principale de l'agent
├── app.py            # Interface Streamlit (chat + dashboard)
├── requirements.txt  # Dépendances Python
├── .env.example      # Template variables d'environnement
├── .env              # Vos vraies clés (à créer, ne pas committer)
├── google_credentials.json  # Credentials Google Service Account
└── GUIDE.md          # Ce fichier
```

---

## ÉTAPE 1 — Prérequis (5 min)

### Python
```bash
python --version   # Besoin de Python 3.10+
```
Si absent : https://www.python.org/downloads/

### Installer les dépendances
```bash
cd agent_seo
pip install -r requirements.txt
```

---

## ÉTAPE 2 — Credentials Google (10 min)

L'agent doit lire/écrire dans votre Google Sheets.
**C'est différent de l'OAuth2 n8n** — ici on utilise un Service Account.

### 2.1 Créer un Service Account

1. Allez sur https://console.cloud.google.com
2. Créez un projet (ou utilisez un existant)
3. Menu → "APIs & Services" → "Credentials"
4. "+ CREATE CREDENTIALS" → "Service account"
5. Donnez un nom : `agent-seo-safia`
6. Cliquez sur le compte créé → onglet "Keys"
7. "ADD KEY" → "Create new key" → JSON
8. Téléchargez le fichier JSON → renommez-le `google_credentials.json`
9. Mettez-le dans le dossier `agent_seo/`

### 2.2 Activer les APIs nécessaires

Dans Google Cloud Console → "APIs & Services" → "Library" :
- Activez **Google Sheets API**
- Activez **Google Drive API**

### 2.3 Partager votre Google Sheet

1. Ouvrez votre Google Sheet
2. Bouton "Partager"
3. Entrez l'email du Service Account (format : `agent-seo-safia@votre-projet.iam.gserviceaccount.com`)
4. Donnez-lui le rôle **Éditeur**
5. Cliquez "Envoyer"

---

## ÉTAPE 3 — Gmail App Password (5 min)

Pour que l'agent envoie des emails sans votre vrai mot de passe :

1. Allez sur https://myaccount.google.com
2. Menu "Sécurité"
3. Activez la **Vérification en 2 étapes** (si pas déjà fait)
4. Cherchez "Mots de passe des applications"
5. Créez un mot de passe pour "Application personnalisée" → `Agent SEO`
6. Copiez le mot de passe généré (16 caractères)

---

## ÉTAPE 4 — Configuration .env (2 min)

```bash
cp .env.example .env
```

Éditez `.env` et remplissez :
- `GMAIL_PASSWORD` → le mot de passe d'application Gmail (16 caractères)
- Les autres valeurs sont déjà pré-remplies avec vos clés actuelles

---

## ÉTAPE 5 — Test rapide (2 min)

### Test 1 : Vérifier la connexion Sheets
```bash
python -c "
from agent import lire_concurrents
concurrents = lire_concurrents()
print(f'✅ {len(concurrents)} concurrents trouvés')
for c in concurrents:
    print(f'  - {c[\"nom\"]} : {c[\"url\"]}')
"
```

### Test 2 : Vérifier Gemini
```bash
python -c "
from agent import appeler_gemini
r = appeler_gemini('Dis bonjour en JSON avec clé message', temperature=0.1, max_tokens=50)
print('✅ Gemini fonctionne:', r)
"
```

### Test 3 : Scraping d'une URL
```bash
python -c "
from agent import scraper_page, parser_html
html = scraper_page('https://example.com')
data = parser_html(html, {'nom':'Test','url':'https://example.com','categorie':'test'})
print('✅ Scraping OK — Title:', data['title'])
"
```

---

## ÉTAPE 6 — Lancer l'agent

### Mode chat interactif (terminal)
```bash
python agent.py
```
Tapez vos questions SEO ou `/analyser` pour lancer l'analyse complète.

### Lancer l'analyse complète depuis terminal
```bash
python agent.py analyser
# ou avec un email spécifique :
python agent.py analyser monmail@gmail.com
```

### Interface web Streamlit (recommandé)
```bash
streamlit run app.py
```
Ouvrez http://localhost:8501 dans votre navigateur.

---

## ÉTAPE 7 — Automatisation hebdomadaire

### Option A : Cron Linux/Mac

```bash
# Ouvrir le crontab
crontab -e

# Ajouter cette ligne (chaque lundi à 7h00)
0 7 * * 1 cd /chemin/vers/agent_seo && python agent.py analyser >> logs/cron.log 2>&1
```

### Option B : Script Python avec schedule

Créez `scheduler.py` :
```python
import schedule, time
from agent import run_analyse_complete

def job():
    print("Démarrage analyse hebdomadaire...")
    run_analyse_complete()

schedule.every().monday.at("07:00").do(job)

print("Scheduler démarré — en attente du lundi 7h...")
while True:
    schedule.run_pending()
    time.sleep(60)
```

Lancez : `python scheduler.py` (en arrière-plan)

---

## ÉTAPE 8 — Déploiement cloud (optionnel)

### Railway.app (le plus simple, gratuit)

1. Créez un compte sur https://railway.app
2. "New Project" → "Deploy from GitHub repo"
3. Connectez votre repo GitHub
4. Ajoutez vos variables d'environnement dans Railway
5. Le fichier `Procfile` suffit :

```
# Procfile
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

### Render.com (alternative gratuite)

1. Créez un compte sur https://render.com
2. "New Web Service" → connectez votre repo
3. Build command : `pip install -r requirements.txt`
4. Start command : `streamlit run app.py --server.port=10000`
5. Ajoutez vos variables d'environnement

---

## Structure Google Sheets attendue

### Onglet "Concurrents"
| Nom du concurrent | URL complète | Catégorie | Statut |
|---|---|---|---|
| Concurrent A | https://... | E-commerce | actif |

### Onglet "snapshots_concurrents"
Colonnes créées automatiquement par l'agent :
`semaine_iso | date_scraping | nom | url | categorie | title | h1 | h2s | meta_desc | mots_cles_principaux | intention_contenu | angle_editorial | strategie_seo | resume_page | score_qualite | points_forts | opportunites | nb_liens | a_schema`

### Onglet "rapports_hebdo"
`semaine_iso | date_rapport | nb_concurrents | nb_opportunites | nb_critiques | score_menace`

---

## Comparaison n8n vs Agent Python

| Fonctionnalité | n8n Workflow | Agent Python |
|---|---|---|
| Scraping | ✅ ScraperAPI | ✅ ScraperAPI |
| Analyse IA | ✅ Gemini | ✅ Gemini |
| Diff N vs N-1 | ✅ | ✅ |
| Email rapport | ✅ | ✅ |
| Google Sheets | ✅ | ✅ |
| Chat interactif | ❌ | ✅ |
| Questions en langage naturel | ❌ | ✅ |
| Dashboard web | ❌ | ✅ |
| Déclenchement à la demande | ❌ | ✅ |
| Gestion erreurs avancée | Basique | ✅ |
| Déploiement | n8n cloud | Railway/Render |

---

## Dépannage

**Erreur "google.auth.exceptions.DefaultCredentialsError"**
→ Vérifiez que `google_credentials.json` est dans le bon dossier

**Erreur "gspread.exceptions.SpreadsheetNotFound"**
→ Vérifiez que vous avez partagé le Sheet avec l'email du Service Account

**Erreur SMTP Gmail**
→ Vérifiez que vous utilisez un App Password et non votre mot de passe normal
→ Vérifiez que la 2FA est activée sur votre compte Google

**Erreur ScraperAPI "No credits"**
→ Vérifiez votre solde sur app.scraperapi.com
→ Le plan gratuit donne 1000 requêtes/mois

**Gemini retourne du JSON vide**
→ Réduisez la taille du texte envoyé (paramètre `slice(0, 3000)`)
→ Vérifiez que la clé API est valide sur aistudio.google.com

# Sistem de Recomandare — HobbyShop

Tema VI la Comerț Electronic: un sistem de recomandare și o aplicație de test.

**HobbyShop** este un magazin online demonstrativ de echipament pentru drumeție, camping, alergare și ciclism. Aplicația recomandă produse **pe baza profilului utilizatorului**: preferințele declarate în setări, completate de produsele pe care le vizualizează, le salvează și le cumpără. Fiecare recomandare vine cu o explicație.

Toate produsele, conturile demonstrative și cumpărăturile sunt date de test.

Echipa: Stoian Cristian-Georgian și Suhan Mihai-Andrei.

## Stiva

| Componentă | Tehnologie |
|---|---|
| Frontend | React (Vite, JavaScript) + Tailwind CSS |
| Backend | FastAPI + scikit-learn |
| Bază de date | SQLite |

## Structura repository-ului

| Director / fișier | Conținut |
|---|---|
| `backend/` | API-ul FastAPI, motorul de recomandare, scriptul de inițializare a datelor, testele |
| `frontend/` | Aplicația React |
| `PropunereProiect.md` | Propunerea proiectului: cerințe, profilul utilizatorului, algoritmul, arhitectura, evaluarea |
| `TemaProiect.txt` | Enunțul temei |

## Pornire

### Backend

Necesită Python 3.11 sau mai nou. Din directorul `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate          # pe Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload      # API: http://127.0.0.1:8000, documentație: http://127.0.0.1:8000/docs
python -m pytest                   # testele
```

Configurarea are valori implicite pentru dezvoltare. Pentru a le schimba, copiază `backend/.env.example` în `backend/.env`:

| Variabilă | Implicit | Rol |
|---|---|---|
| `HOBBYSHOP_DATABASE_PATH` | `data/hobbyshop.db` | Fișierul SQLite, relativ la `backend/`; se creează la pornire |
| `HOBBYSHOP_SECRET_KEY` | o cheie de dezvoltare | Cheia pentru semnarea token-urilor de autentificare |
| `HOBBYSHOP_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Adresele de unde frontendul poate apela API-ul |

Structura backendului:

| Fișier | Rol |
|---|---|
| `app/main.py` | Crearea aplicației FastAPI, CORS, înregistrarea rutelor |
| `app/config.py` | Setările, citite din variabile de mediu sau din `.env` |
| `app/db.py` | Conexiunea SQLite (SQLModel), cu cheile externe activate pe fiecare conexiune |
| `app/dependencies.py` | Dependențe comune, de exemplu sesiunea de bază de date (`SessionDep`) |
| `app/routers/` | Rutele API, câte un fișier pe zonă (`health.py`, …) |
| `tests/` | Testele pytest; fiecare test folosește o bază de date temporară |

### Frontend

Necesită Node.js 20 sau mai nou. Din directorul `frontend/`:

```bash
npm install
npm run dev        # aplicația: http://localhost:5173
npm run build      # build de producție în dist/
```

Backendul trebuie să ruleze în paralel (vezi mai sus). Indicatorul din bara de navigare arată dacă frontendul ajunge la `GET /health`.

Adresa API-ului se configurează prin `VITE_API_URL`. Pentru a o schimba, copiază `frontend/.env.example` în `frontend/.env.local`:

| Variabilă | Implicit | Rol |
|---|---|---|
| `VITE_API_URL` | `http://127.0.0.1:8000` | Adresa backendului FastAPI |

Structura frontendului:

| Fișier / director | Rol |
|---|---|
| `src/main.jsx` | Punctul de intrare: React + `BrowserRouter` |
| `src/App.jsx` | Rutele aplicației |
| `src/components/Layout.jsx` | Layout-ul comun: bara de navigare, conținutul, subsolul |
| `src/lib/api.js` | Modulul pentru apelurile către API (`api.get`, `api.post`, …, `getHealth`); toate paginile îl folosesc |
| `src/pages/` | Câte o pagină pe rută |
| `src/index.css` | Tailwind CSS (v4, prin pluginul `@tailwindcss/vite`) |

Rutele:

| Rută | Pagină |
|---|---|
| `/autentificare` | Autentificare |
| `/inregistrare` | Înregistrare |
| `/setari` | Setări de profil |
| `/catalog` | Catalog (pagina de start) |
| `/produs/:id` | Pagina de produs |
| `/recomandari` | Recomandate pentru tine |
| `/profil` | Profilul meu de recomandare |
| `/evaluare` | Evaluare |

## Cum lucrăm

### Task-uri

Task-urile sunt în Linear, în proiectul **Sistem-de-Recomandare**.

- Titlul fiecărui task începe cu numărul pasului: „Pas 01 · …” până la „Pas 24 · …”. Pașii dau ordinea de lucru. Ca să-i vezi în ordine, sortează lista după titlu.
- Fiecare își ia următorul pas atribuit lui. Un pas poate începe când pașii de care depinde sunt gata; nota de la începutul fiecărui task spune care sunt aceștia.
- Când începi un task, îl muți în **In Progress**; când Pull Request-ul e aprobat și unit în `main`, îl muți în **Done**.

### Branch-uri și Pull Request-uri

1. Pentru fiecare task faci un branch din `main` actualizat. Folosește numele generat de Linear (în task: **Copy git branch name**), de exemplu `bibozisbibogel/cri-6-pas-02-schelet-backend-fastapi-conexiune`. Identificatorul `cri-6` din nume leagă automat branch-ul de task.
2. Lucrezi și faci commit-uri doar pe branch-ul tău, cu mesaje scurte care spun ce s-a schimbat.
3. Deschizi un Pull Request în `main`, cu identificatorul task-ului în titlu, de exemplu `CRI-6: schelet backend FastAPI`.
4. Celălalt coleg revizuiește Pull Request-ul. Se unește în `main` numai după aprobare și cu testele trecute.
5. După unire, ștergi branch-ul.

Nu facem push direct în `main`. Singura excepție a fost configurarea inițială a repository-ului (pasul 01).

### Reguli comune

- `main` trebuie să pornească și să treacă testele în orice moment.
- Formatul datelor dintre frontend și backend (endpoint-uri, câmpuri JSON, valorile permise în profil) este cel din contractul API (pasul 04, CRI-8). Dacă trebuie schimbat, îl schimbăm întâi acolo și îl anunțăm celuilalt.
- Fișierele generate nu intră în repository: baza de date SQLite, `node_modules/`, mediile virtuale Python, build-urile. Lista completă e în `.gitignore`.

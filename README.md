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
| `docs/api.md` | Contractul API: endpoint-urile, formatul JSON, valorile permise, tabelele |
| `docs/testare.md` | Lista de verificare a fluxului complet (cont nou, schimbarea setărilor, comportament, conturile demo, cazuri limită) și rezultatele ei |
| `docs/prezentare/Prezentare.pptx` | Prezentarea (partea teoretică): partea 1 Suhan, partea 2 Cristian, în același fișier |
| `PropunereProiect.md` | Propunerea proiectului: cerințe, profilul utilizatorului, algoritmul, arhitectura, evaluarea |
| `TemaProiect.txt` | Enunțul temei |

## Pornire rapidă

Ai nevoie de **Python 3.11+** și **Node.js 20+**. Pornești două servere, fiecare în terminalul lui, din rădăcina repository-ului.

**Terminalul 1, backendul:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # pe Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.seed --reset         # catalogul, conturile demo și clienții simulați
uvicorn app.main:app --reload      # http://127.0.0.1:8000 (documentația API: /docs)
```

**Terminalul 2, frontendul:**

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

Deschide http://localhost:5173. În bara de sus, indicatorul „API conectat” arată că frontendul ajunge la backend. Te poți autentifica cu un cont demo:

| Cont | E-mail | Parolă |
|---|---|---|
| Maria | `maria@example.com` | `maria2026` |
| Radu | `radu@example.com` | `radu2026` |

Detaliile pentru fiecare parte sunt mai jos, la [Pornire](#pornire). Scenariul pentru prezentare e la [Scenariul de demonstrație](#scenariul-de-demonstrație-5-minute).

## Pornire

### Backend

Necesită Python 3.11 sau mai nou. Din directorul `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate          # pe Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m app.seed                 # încarcă datele de test; se poate rula de mai multe ori
python -m app.seed --reset         # șterge TOATE datele și le recreează (de exemplu înainte de prezentare)
uvicorn app.main:app --reload      # API: http://127.0.0.1:8000, documentație: http://127.0.0.1:8000/docs
python -m pytest                   # testele
```

#### Date de test

`python -m app.seed` încarcă:

- **catalogul:** 132 de produse de test;
- **două conturi demonstrative**, cu date complet diferite:

  | Cont | E-mail | Parolă | Profil |
  |---|---|---|---|
  | Maria | `maria@example.com` | `maria2026` | alergare (mult), începătoare, buget redus, vară, buget maxim 300 lei; istoric doar cu produse de alergare |
  | Radu | `radu@example.com` | `radu2026` | camping și drumeție (mult), avansat, rezistență, iarnă, buget maxim 5000 lei; istoric doar cu produse de camping și drumeție |

  Cele două profiluri nu au nicio activitate, niciun stil și niciun sezon în comun. Primele 10 recomandări ale lor nu au niciun produs comun.
- **300 de clienți simulați** (`client001@simulat.example.com` …):
  - setări de profil și istoric pe 90 de zile (1 august – 30 octombrie 2026), generate cu seed fix;
  - folosiți pentru popularitate (rezerva motorului) și pentru evaluare;
  - nu se pot autentifica.

Fără `--reset`, scriptul completează doar ce lipsește și nu atinge conturile create din aplicație. Cu `--reset`, șterge totul, inclusiv conturile create din aplicație, și recreează aceleași date. Domeniul `example.com` e rezervat pentru exemple, deci nu aparține nimănui.

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
| `app/models.py` | Tabelele bazei de date (`users`, `user_profiles`, `products`, `interactions`, `favorites`, `recommendation_feedback`) |
| `app/vocabulary.py` | Valorile permise (activități, nivel, stiluri, sezon, tipuri de evenimente) și etichetele lor |
| `app/recommender/` | Motorul de recomandare (scikit-learn), independent de baza de date și de API |
| `app/evaluation.py` | Evaluarea offline: popularitate vs. recomandarea bazată pe profil (`python -m app.evaluation`, `GET /evaluation`) |
| `app/recommendation_service.py` | Legătura motorului cu baza de date: vectorii produselor (recalculați doar când se schimbă catalogul), profilul, istoricul, popularitatea |
| `app/schemas.py` | Formatul JSON al cererilor și răspunsurilor (Pydantic) |
| `app/security.py` | Hash-ul parolelor (bcrypt) și token-urile de autentificare (JWT, valabile 7 zile) |
| `app/dependencies.py` | Dependențe comune: sesiunea de bază de date (`SessionDep`) și utilizatorul autentificat (`CurrentUserDep`, 401 fără token valid) |
| `app/routers/` | Rutele API, câte un fișier pe zonă (`health.py`, `vocabulary.py`, `auth.py`, `products.py`, `profile.py`, `interactions.py`, `recommendations.py`) |
| `app/seed/` | Scriptul de inițializare (`python -m app.seed [--reset]`): `catalog.py` (produsele, în liniile Start / Activ / Pro), `demo.py` (Maria și Radu), `simulation.py` (clienții simulați), `timeline.py` (perioada simulată) |
| `tests/` | Testele pytest; fiecare test folosește o bază de date temporară |

Tabelele se creează la pornire, dar cele existente nu se modifică (nu folosim migrări). După o schimbare în `app/models.py`, șterge `backend/data/hobbyshop.db`.

Formatul tuturor endpoint-urilor, inclusiv al celor care urmează, este în [docs/api.md](docs/api.md).

#### Motorul de recomandare

`app/recommender/` recomandă produse pe baza profilului utilizatorului, prin filtrare bazată pe conținut:

- **Vectorii produselor** (`engine.py`): fiecare produs are un vector cu două părți, normalizate separat:
  - preferințele: categorie, utilizări, niveluri, stiluri, sezoane (`DictVectorizer`);
  - textul: nume, etichete, descriere (`TfidfVectorizer`), cu pondere mai mică.
- **Profilul declarat** (`features.py`): setările utilizatorului se traduc în aceleași caracteristici.
  - Activitățile contează cel mai mult (intensitate „mult” = 1, „puțin” = 0,5), apoi stilurile, nivelul și sezonul.
  - Nivelurile vecine și echipamentul „tot anul” se potrivesc parțial.
- **Profilul din comportament** (`behavior.py`): suma ponderată a vectorilor produselor din istoric.
  - Ponderile vin din curs: vizualizare = 1 (cel mult 3 per produs, ca refresh-urile să nu conteze), favorit = 5, cumpărare = 10.
  - Favoritele urmează ultima acțiune (adăugat / scos).
- **Profilul final** (`recommend.py`): `α × profil declarat + (1 − α) × profil din comportament`, cu α = 0,75, ales la evaluare (vezi mai jos). Dacă lipsește una dintre părți, se folosește cealaltă.
- **Scorul** este similaritatea cosinus dintre profil și produs.
- **Lista finală** păstrează doar produsele disponibile, sub bugetul din profil, necumpărate și neexcluse (de exemplu produsul deschis în pagină).
- **Rezerva:** fără setări și fără istoric, sau dacă nimic nu se potrivește, se recomandă produsele cu cei mai mulți cumpărători. Motivul se trimite în `fallback_reason`.
- **Explicațiile:** fiecare recomandare primește:
  - preferințele alese explicit în setări care se regăsesc în produs („pentru că ai ales alergare și buget redus”);
  - produsele din istoric care au influențat-o cel mai mult („seamănă cu …, din favoritele tale”).
- **Produsele similare** cu un produs dat au și ele explicație, cu caracteristicile comune.

Ponderile sunt constante la începutul fișierelor `features.py`, `behavior.py` și `recommend.py`.

#### Evaluarea offline

```bash
python -m app.evaluation           # afișează rezultatele în terminal; aceleași date sunt la GET /evaluation
```

`app/evaluation.py` compară popularitatea cu recomandarea bazată pe profil, pe istoricul celor 300 de clienți simulați:

- **Împărțirea:** istoricul de 90 de zile se împarte cronologic în antrenare (zilele 0–60), validare (60–75) și test (75–90).
- **Fără scurgeri de informație:** profilurile din comportament și popularitatea se construiesc doar din evenimentele de dinaintea fiecărui interval.
- **Relevant** înseamnă un produs cumpărat în interval, încă disponibil și necumpărat înainte.
- **Metrici:** Precision@5, Recall@5, acoperirea catalogului și timpul de răspuns. Clienții fără istoric se raportează separat.
- **Alegerea ponderilor:** pe validare, dintre α ∈ {0; 0,25; 0,5; 0,75; 1} și ponderile acțiunilor (curs 1/5/10 sau egale). A câștigat α = 0,75 cu ponderile din curs, pe care le folosește acum aplicația.

Rezultatele pe test, cu datele implicite (`python -m app.seed --reset`):

| Configurație | Precision@5 | Recall@5 | Acoperire |
|---|---|---|---|
| Popularitate | 0,044 | 0,164 | 7,5% |
| Profil, α = 0,75 (aplicația) | 0,090 | 0,304 | 90,8% |
| Profil, α = 0,5 (ponderile inițiale) | 0,097 | 0,316 | 89,2% |

Concluziile:

- Recomandarea bazată pe profil găsește de aproximativ două ori mai multe produse relevante decât popularitatea și folosește aproape tot catalogul, nu doar câteva produse.
- Pe validare, combinația dintre setări și comportament e mai bună decât fiecare sursă luată separat.
- Pe test, α = 0,5 iese ușor peste α = 0,75. Cu ~114 clienți evaluați, diferența nu e concludentă, iar alegerea rămâne cea făcută pe validare.

**Datele sunt sintetice:** rezultatele descriu comportamentul simulatorului din `app/seed/simulation.py`, nu preferințe reale.

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
| `src/lib/api.js` | Modulul pentru apelurile către API (`api.get`, `api.post`, …); trimite automat token-ul și transformă erorile în mesaje (`errorMessage`, `fieldErrors`) |
| `src/lib/auth.jsx` | `AuthProvider` și `useAuth()`: contul curent, `login`, `register`, `logout`; token-ul se păstrează în `localStorage` |
| `src/components/RequireAuth.jsx` | Rutele protejate (fără cont → `/autentificare`) și cele doar pentru vizitatori |
| `src/components/Form.jsx` | Componente comune de formular (câmp, eroare, buton) |
| `src/lib/vocabulary.js` | `useVocabulary()`: etichetele în română din `GET /vocabulary` (cerute o singură dată) |
| `src/lib/format.js` | Formatarea prețurilor (RON) și a datelor |
| `src/lib/interactions.js` | `sendInteraction()` (cu id unic de eveniment) și `useHistory()` (`GET /me/history`) |
| `src/components/ProductCard.jsx` | Cardul unui produs, folosit în catalog și la recomandări |
| `src/components/RecommendationList.jsx` | Lista de recomandări sau de produse similare, cu potrivirea și explicația fiecărui produs și mesajul pentru rezervă |
| `src/components/RecommendedStrip.jsx` | Secțiunea scurtă „Recomandate pentru tine” din catalog și de pe pagina de produs; pentru vizitatori, invitația de a-și crea cont |
| `src/lib/recommendations.js` | `useRecommendations` și `useSimilarProducts`: încarcă listele și le reîncarcă la schimbarea contului sau a datelor utilizatorului |
| `src/lib/userData.js` | `notifyUserDataChanged()`: se apelează după ce utilizatorul salvează setările sau face o acțiune (favorit, cumpărare), ca recomandările afișate să se actualizeze singure |
| `src/components/Status.jsx` | Stările comune: eroare, listă goală, „Date de test”, disponibilitate |
| `src/pages/` | Câte o pagină pe rută |
| `src/index.css` | Tailwind CSS (v4, prin pluginul `@tailwindcss/vite`) |

Rutele:

| Rută | Pagină | Acces |
|---|---|---|
| `/autentificare` | Autentificare | doar fără cont |
| `/inregistrare` | Înregistrare (apoi direct la setări) | doar fără cont |
| `/setari` | Setări de profil: activități cu intensitate, nivel, stiluri, sezon, buget; deschisă automat după înregistrare | cu cont |
| `/catalog` | Catalog (pagina de start); filtrele stau în adresă (`?categorie=…&q=…&pret_maxim=…&disponibile=1&pagina=…`) | public |
| `/produs/:id` | Pagina de produs; cu cont, deschiderea trimite o vizualizare și apar butoanele de favorite și cumpărare (simulată) | public |
| `/recomandari` | Recomandate pentru tine | cu cont |
| `/profil` | Profilul meu de recomandare | cu cont |
| `/istoric` | Favorite și istoric: favoritele, cumpărăturile și ultimele 50 de evenimente | cu cont |
| `/evaluare` | Evaluare | public |

## Scenariul de demonstrație (~5 minute)

Arată cele trei cerințe de la laborator:
- recomandarea pe baza profilului;
- două conturi cu date complet diferite;
- un cont nou creat de la zero și configurat.

Slide-ul „Demonstrația” din prezentare are aceiași pași.

### Înainte de prezentare

1. Recreează datele, ca să pornești de la aceeași stare: `python -m app.seed --reset` (în `backend/`). Șterge și conturile create la repetiții.
2. Rulează testele: `python -m pytest` (în `backend/`) și `npm run build` (în `frontend/`).
3. Pornește cele două servere (vezi [Pornire rapidă](#pornire-rapidă)) și verifică indicatorul „API conectat”.

### Pașii

| # | Ce faci | Ce arăți |
|---|---|---|
| 1 | **Autentificare** cu `maria@example.com` / `maria2026`, apoi **Recomandări** | Produse pentru alergare, cele mai multe din linia „Start” pentru începători, toate sub 300 lei. Sub fiecare, explicația: „Pentru că ai ales alergare, buget redus și începător; seamănă cu «Pantofi de alergare pe șosea Ritm Start», din cumpărăturile tale.” |
| 2 | **Profilul meu** | Din ce se formează profilul: 75% setări, 25% comportament. Interesele dominante: alergare, buget redus, începător, vară. Produsele din istoric. |
| 3 | **Deconectare**, autentificare cu `radu@example.com` / `radu2026`, **Recomandări** | Listă complet diferită: camping și drumeție de iarnă, echipament rezistent. Primele 10 recomandări ale celor doi nu au niciun produs comun. |
| 4 | **Deconectare**, **Înregistrare** cu un e-mail nou (de exemplu `demo@example.com`) → **Creează contul** | Contul nou ajunge direct în **Setări profil**. |
| 5 | Ciclism: **Mult**; nivel **Intermediar**; stil **Ultraușor**; buget **500**; **Salvează setările**, apoi **Recomandări** | Recomandări personalizate imediat, fără istoric: ciclism, sub 500 lei, cu explicații („Pentru că ai ales ciclism și ultraușor”). |
| 6 | Înapoi în **Setări**: ciclism → **Deloc**, alergare → **Mult**, buget **200** → **Salvează setările**, apoi **Recomandări** | Lista se schimbă complet: alergare, sub 200 lei. |
| 7 | Deschide un produs din listă → **☆ Adaugă la favorite**, apoi **Recomandări** | Ordinea se schimbă, iar explicațiile pomenesc favoritul („… din favoritele tale”). Un produs cumpărat cu **Cumpără (simulat)** nu mai apare în recomandări. |
| 8 | **Evaluare** | Recomandarea pe profil găsește de ~1,9 ori mai multe produse relevante decât popularitatea (Recall@5 0,304 față de 0,164) și acoperă ~91% din catalog. Datele sunt sintetice. |

Dacă repeți demonstrația fără `--reset`, folosește alt e-mail la pasul 4.

Verificările făcute pentru acest scenariu, automat prin API și manual în browser, sunt în [docs/testare.md](docs/testare.md).

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

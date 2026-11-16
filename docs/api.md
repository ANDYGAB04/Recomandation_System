# Contractul API — HobbyShop

Acest document fixează formatul datelor dintre frontend (React) și backend (FastAPI). Îl folosim amândoi ca referință: backendul îl implementează, frontendul se bazează pe el.

Dacă trebuie schimbat ceva, schimbăm întâi acest fișier, printr-un Pull Request aprobat de celălalt, și abia apoi codul.

Documentația generată automat de FastAPI (`/docs`) arată endpoint-urile deja implementate. Acest document le descrie și pe cele care urmează.

## Reguli generale

- **Adresa:** `http://127.0.0.1:8000` în dezvoltare (`VITE_API_URL` în frontend).
- **Format:** JSON în UTF-8, în cereri și în răspunsuri.
- **Identificatori:** numere întregi (`id`). Prețurile și bugetele sunt în lei, ca numere zecimale.
- **Momente de timp:** text ISO 8601 în UTC, de exemplu `"2026-11-15T14:30:00Z"`.
- **Valori fixe** (activități, nivel, stiluri, sezon, intensitate, tipuri de evenimente): identificatorii din `GET /vocabulary`. Frontendul afișează etichetele, nu identificatorii.

### Autentificare

Endpoint-urile marcate cu 🔒 cer antetul:

```
Authorization: Bearer <access_token>
```

Token-ul vine de la `POST /auth/register` sau `POST /auth/login`. Este un JWT semnat cu `HOBBYSHOP_SECRET_KEY` și expiră după 7 zile. Frontendul îl păstrează în `localStorage`.

Fără token sau cu un token invalid ori expirat, răspunsul este `401`, iar frontendul trimite utilizatorul la pagina de autentificare.

### Erori

Erorile au forma standard FastAPI:

```json
{ "detail": "Există deja un cont cu acest e-mail." }
```

- `detail` este un mesaj în română, gata de afișat utilizatorului.
- Excepție: la `422` (date invalide), FastAPI întoarce în `detail` o listă cu câmpurile greșite. Frontendul afișează mesajele lângă câmpurile respective.

| Cod | Când |
|---|---|
| `200` / `201` | Succes (`201` la creare) |
| `401` | Lipsește autentificarea sau e-mailul ori parola sunt greșite |
| `404` | Resursa nu există |
| `409` | Conflict: e-mail deja folosit, produs indisponibil sau deja cumpărat |
| `422` | Date invalide: câmp lipsă, valoare necunoscută, număr negativ |

## Valorile permise

Sursa lor este `backend/app/vocabulary.py`. Ruta `GET /vocabulary` le întoarce împreună cu etichetele.

| Grup | Valori (etichetă) |
|---|---|
| `activities` | `hiking` (Drumeție), `camping` (Camping), `running` (Alergare), `cycling` (Ciclism) |
| `intensities` | `low` (Puțin), `high` (Mult) |
| `levels` | `beginner` (Începător), `intermediate` (Intermediar), `advanced` (Avansat) |
| `styles` | `ultralight` (Ultraușor), `comfort` (Confort), `durable` (Rezistență), `performance` (Performanță), `budget` (Buget redus) |
| `seasons` | `summer` (Vară), `winter` (Iarnă), `all_year` (Tot anul) |
| `event_types` | `view` (Vizualizare), `favorite` (Adăugat la favorite), `unfavorite` (Scos din favorite), `purchase` (Cumpărare) |

Aceleași valori apar și în profil, și în produse. Așa, motorul de recomandare compară direct preferințele utilizatorului cu caracteristicile produselor.

## Obiecte comune

### Produs

```json
{
  "id": 12,
  "name": "Cort Ultralight 2P",
  "category": "camping",
  "usages": ["camping", "hiking"],
  "levels": ["intermediate", "advanced"],
  "styles": ["ultralight"],
  "seasons": ["summer"],
  "tags": ["cort", "2 persoane"],
  "description": "Cort de 1,4 kg pentru ture de mai multe zile.",
  "price": 899.99,
  "available": true,
  "is_test_data": true
}
```

| Câmp | Descriere |
|---|---|
| `category` | Activitatea principală (o valoare din `activities`) |
| `usages` | Toate activitățile potrivite, inclusiv `category` |
| `levels`, `styles`, `seasons` | Liste cu valori din `GET /vocabulary`; o listă goală înseamnă „oricare” |
| `tags` | Etichete libere, descriptive, folosite la căutare și în explicații |

### Profil

```json
{
  "activities": { "running": "high", "cycling": "low" },
  "level": "beginner",
  "styles": ["budget"],
  "season": "summer",
  "max_budget": 300,
  "is_complete": true,
  "updated_at": "2026-11-15T14:30:00Z"
}
```

| Câmp | Descriere |
|---|---|
| `activities` | Activitate → intensitate (`low` / `high`); cel puțin una pentru un profil complet |
| `level`, `season` | O valoare sau `null` (necompletat) |
| `styles` | Zero sau mai multe valori |
| `max_budget` | Buget maxim per produs, în lei, sau `null` (fără limită) |
| `is_complete` | `true` dacă are cel puțin o activitate. Doar în răspunsuri: frontendul îl folosește ca să trimită contul nou la setări |

## Endpoint-uri

Coloana „Pas” arată task-ul din Linear care implementează endpoint-ul.

| Endpoint | Pas | Cine |
|---|---|---|
| `GET /health` | 02 (CRI-6) | Cristian — gata |
| `GET /vocabulary` | 04 (CRI-8) | Cristian — gata |
| `POST /auth/register`, `POST /auth/login`, `GET /auth/me` | 07 (CRI-9) | Suhan— gata |
| `GET /products`, `GET /products/{id}` | 08 (CRI-10) | Suhan — gata |
| `GET /profile`, `PUT /profile` | 10 (CRI-12) | Suhan— gata |
| `POST /interactions`, `GET /me/history` | 11 (CRI-13) | Suhan— gata |
| `GET /recommendations`, `GET /recommendations/profile`, `GET /products/{id}/similar` | 14 (CRI-20) | Cristian |
| `GET /evaluation` | 20 (CRI-23) | Cristian |

### Sistem

#### `GET /health`

```json
{ "status": "ok", "database": "ok" }
```

#### `GET /vocabulary`

```json
{
  "activities": [{ "value": "hiking", "label": "Drumeție" }, "…"],
  "intensities": ["…"],
  "levels": ["…"],
  "styles": ["…"],
  "seasons": ["…"],
  "event_types": ["…"]
}
```

### Conturi

#### `POST /auth/register`

Creează contul și un profil gol, apoi întoarce direct un token. Așa, utilizatorul nou ajunge în setări fără să se mai autentifice o dată.

Cerere:

```json
{ "email": "ana@exemplu.ro", "password": "parola-secreta", "display_name": "Ana" }
```

- `email`: adresă validă; se compară fără să conteze literele mari sau mici și se salvează cu litere mici.
- `password`: minimum 8 caractere; se salvează doar ca hash.
- `display_name`: 1–100 de caractere.

Răspuns `201`:

```json
{
  "access_token": "eyJhbGciOi…",
  "token_type": "bearer",
  "user": { "id": 3, "email": "ana@exemplu.ro", "display_name": "Ana" }
}
```

Erori: `409` „Există deja un cont cu acest e-mail.”, `422`.

#### `POST /auth/login`

Cerere: `{ "email": "…", "password": "…" }`. Răspuns `200`: la fel ca la înregistrare.

Erori: `401` „E-mail sau parolă greșită.” (același mesaj în ambele cazuri, ca să nu dezvăluie ce conturi există).

#### `GET /auth/me` 🔒

```json
{ "id": 3, "email": "ana@exemplu.ro", "display_name": "Ana", "created_at": "2026-11-15T14:30:00Z" }
```

### Profil

#### `GET /profile` 🔒

Întoarce profilul utilizatorului autentificat (obiectul **Profil**). Un cont nou are `activities: {}`, `styles: []`, celelalte câmpuri `null` și `is_complete: false`.

#### `PUT /profile` 🔒

Înlocuiește toate setările. Cererea conține câmpurile `activities`, `level`, `styles`, `season`, `max_budget`; un câmp lipsă înseamnă „necompletat”.

```json
{
  "activities": { "running": "high" },
  "level": "beginner",
  "styles": ["budget", "comfort"],
  "season": "summer",
  "max_budget": 300
}
```

Răspuns `200`: profilul salvat. Erori: `422` pentru valori care nu sunt în `GET /vocabulary`, pentru stiluri duplicate sau pentru un buget mai mic sau egal cu 0.

### Catalog

#### `GET /products`

Parametri (toți opționali):

| Parametru | Descriere |
|---|---|
| `category` | O valoare din `activities` |
| `q` | Caută în nume, descriere și `tags`, fără să conteze literele mari sau mici |
| `max_price` | Preț maxim |
| `available_only` | `true` pentru a ascunde produsele indisponibile |
| `limit` | Implicit 24, maximum 100 |
| `offset` | Implicit 0 |

Răspuns `200`, ordonat după `id`:

```json
{ "items": ["…produse…"], "total": 138, "limit": 24, "offset": 0 }
```

#### `GET /products/{id}`

Răspuns `200`: un **Produs**. Erori: `404` „Produsul nu există.”

### Interacțiuni

#### `POST /interactions` 🔒

Cerere:

```json
{ "event_id": "3f1c9a2e-…", "product_id": 12, "type": "favorite" }
```

- `event_id`: generat de frontend (de exemplu `crypto.randomUUID()`), maximum 64 de caractere, unic pentru fiecare acțiune.
- `type`: o valoare din `event_types`.
- Evenimentele `favorite` / `unfavorite` actualizează și lista de favorite, în aceeași tranzacție.

Răspuns `201` pentru un eveniment nou:

```json
{ "event_id": "3f1c9a2e-…", "recorded": true }
```

Dacă același `event_id` a fost deja salvat, răspunsul este `200`, cu `"recorded": false`, iar evenimentul nu se salvează a doua oară.

Erori:
- `404` „Produsul nu există.”;
- `409` „Produsul nu este disponibil.” (la `purchase`);
- `409` „Ai cumpărat deja acest produs.” (la `purchase`);
- `422`.

#### `GET /me/history` 🔒

```json
{
  "favorites": ["…produse…"],
  "purchases": [{ "product": { "…": "…" }, "purchased_at": "2026-11-15T14:30:00Z" }],
  "events": [
    { "event_id": "…", "type": "view", "product": { "id": 12, "name": "Cort Ultralight 2P" }, "created_at": "…" }
  ]
}
```

`events` conține ultimele 50 de evenimente, cele mai noi primele.

### Recomandări

#### `GET /recommendations` 🔒

Parametri: `k` (implicit 10, maximum 50) și `exclude` (id-ul unui produs, se poate repeta, de exemplu produsul deschis în pagină).

```json
{
  "strategy": "personalized",
  "fallback_reason": null,
  "items": [
    {
      "product": { "…": "…" },
      "score": 0.83,
      "explanation": {
        "text": "Pentru că ai ales alergare și buget redus; seamănă cu Pantofii Trail pe care i-ai salvat.",
        "matched": [
          { "group": "activities", "value": "running", "label": "Alergare" },
          { "group": "styles", "value": "budget", "label": "Buget redus" }
        ],
        "because_of": [{ "id": 7, "name": "Pantofi de alergare Trail" }]
      }
    }
  ]
}
```

| Câmp | Descriere |
|---|---|
| `strategy` | `personalized` (din profil) sau `popular` (rezervă) |
| `fallback_reason` | `null`, sau motivul rezervei, de exemplu „Completează setările de profil pentru recomandări personalizate.” |
| `score` | Similaritatea cu profilul, între 0 și 1. Pentru `popular`: numărul de cumpărători |
| `explanation.text` | Fraza afișată sub produs |
| `explanation.matched` | Preferințele din profil care au contribuit la scor |
| `explanation.because_of` | Produsele din istoric care au influențat recomandarea |

Nu se recomandă niciodată produse deja cumpărate, indisponibile, peste `max_budget` sau din `exclude`.

#### `GET /recommendations/profile` 🔒

Datele pentru pagina „Profilul meu de recomandare”:

```json
{
  "sources": { "declared": 0.5, "behavior": 0.5 },
  "interests": [{ "group": "activities", "value": "running", "label": "Alergare", "weight": 0.61 }],
  "top_products": [{ "product": { "id": 7, "name": "Pantofi de alergare Trail" }, "weight": 10, "events": ["purchase"] }]
}
```

#### `GET /products/{id}/similar`

Autentificarea e opțională. Cu token, se exclud produsele cumpărate de utilizator. Parametru: `k` (implicit 4).

```json
{
  "items": [
    {
      "product": { "…": "…" },
      "score": 0.77,
      "explanation": { "text": "Caracteristici comune: camping, ultraușor.", "matched": ["…"], "because_of": [] }
    }
  ]
}
```

Erori: `404` „Produsul nu există.”

### Evaluare

#### `GET /evaluation`

```json
{
  "k": 5,
  "note": "Date sintetice: rezultatele descriu comportamentul simulatorului, nu preferințe reale.",
  "selected_config": "…",
  "validation": { "start": "…", "end": "…", "users_evaluated": 120, "users_without_relevant": 280, "users_without_history": 3, "results": ["…rânduri…"] },
  "test": { "…": "aceeași formă" }
}
```

Un rând din `results`:

```json
{ "config": "popularitate", "strategy": "popular", "precision_at_k": 0.06, "recall_at_k": 0.22, "coverage": 0.07, "latency_ms": 0.05, "users": 129 }
```

## Baza de date

Tabelele sunt definite în `backend/app/models.py` și se creează la pornirea API-ului.

| Tabelă | Conținut |
|---|---|
| `users` | e-mail (unic), hash-ul parolei, nume afișat, data creării |
| `user_profiles` | datele declarate: `activities` (JSON), `level`, `styles` (JSON), `season`, `max_budget`; una pe utilizator |
| `products` | catalogul; listele (`usages`, `levels`, `styles`, `seasons`, `tags`) sunt JSON |
| `interactions` | `event_id` (unic), utilizator, produs, tip, moment |
| `favorites` | starea curentă a favoritelor (utilizator, produs) |

Regulile verificate chiar de baza de date:
- e-mailul și `event_id` sunt unice;
- prețul este `>= 0`, iar bugetul este `> 0`;
- tipul evenimentului este unul din `event_types`;
- cheile externe sunt valide.

Ștergerea unui utilizator îi șterge profilul, interacțiunile și favoritele.

Nu folosim migrări. Dacă se schimbă un model, se șterge `backend/data/hobbyshop.db`, iar baza de date se recreează la pornire. Scriptul de inițializare (`python -m app.seed`) încarcă deocamdată catalogul (pasul 08); conturile demo și clienții simulați vin la pasul 12 (CRI-19).

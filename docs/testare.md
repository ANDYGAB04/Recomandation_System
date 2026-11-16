# Testarea fluxului complet

Lista de verificare pentru pasul 22 (CRI-25): verificăm, ca la laborator, că aplicația funcționează cap-coadă, de la un cont nou până la cele două conturi demo.

Verificarea a fost făcută pe 16 noiembrie 2026, pe datele complete: `python -m app.seed --reset`, cu 132 de produse, conturile Maria și Radu și 300 de clienți simulați.

## Cum se repetă

**Automat**, prin API. Din `backend/`:

```bash
python -m pytest tests/test_full_flow.py
```

Câte un test pentru fiecare scenariu de mai jos, pe o bază de date temporară cu toate datele de test.

**Manual, în browser**, înainte de prezentare:

```bash
cd backend && python -m app.seed --reset && uvicorn app.main:app --reload
cd frontend && npm run dev          # http://localhost:5173
```

Conturile demo:

| Cont | E-mail | Parolă |
|---|---|---|
| Maria | `maria@example.com` | `maria2026` |
| Radu | `radu@example.com` | `radu2026` |

## Rezultate

Coloana **API** arată verificarea prin API, făcută și automat (`tests/test_full_flow.py`). Coloana **Browser** se bifează la verificarea manuală în interfață.

### 1. Cont nou de la zero

| Verificare | API | Browser |
|---|---|---|
| Înregistrarea creează contul și duce la setări (profil gol, `is_complete: false`) | ✅ | ☐ |
| Setările „ciclism (mult), intermediar, ultraușor, buget 500 lei” se salvează | ✅ | ☐ |
| Recomandările sunt personalizate, toate de ciclism, toate sub 500 lei, toate disponibile | ✅ | ☐ |
| Fiecare recomandare are o explicație („Pentru că ai ales ciclism și ultraușor.”) | ✅ | ☐ |
| Produsele ultraușoare sunt primele în listă | ✅ | ☐ |
| Setările apar precompletate după deconectare și o nouă autentificare | ✅ | ☐ |

Observație: la prima verificare, doar 3 din primele 10 produse erau ultraușoare, toate din linia Pro, pentru avansați. Cauza era catalogul, nu motorul (CRI-30). După corectare sunt 6 din 10, iar primele trei se potrivesc la toate criteriile: ciclism, ultraușor, intermediar.

### 2. Schimbarea setărilor

| Verificare | API | Browser |
|---|---|---|
| Ciclism → alergare cu buget 200 lei: lista se schimbă complet (niciun produs comun) | ✅ | ☐ |
| Noua listă are doar produse de alergare, sub 200 lei | ✅ | ☐ |
| După salvarea setărilor, recomandările se reîncarcă fără reîncărcarea paginii | — | ☐ |

### 3. Comportament

| Verificare | API | Browser |
|---|---|---|
| Trei vizualizări și un favorit pe un produs schimbă ordinea listei; produsul urcă în primele 5 | ✅ | ☐ |
| Explicațiile menționează produsul favorit („seamănă cu … din favoritele tale”) | ✅ | ☐ |
| Un produs cumpărat dispare din recomandări și din produsele similare | ✅ | ☐ |
| Un eveniment retrimis cu același `event_id` se salvează o singură dată | ✅ | ☐ (dublu click pe butoane) |
| Butoanele de favorite și cumpărare păstrează starea după reîncărcarea paginii | — | ☐ |

### 4. Cele două conturi demo

| Verificare | API | Browser |
|---|---|---|
| Maria și Radu primesc recomandări personalizate | ✅ | ☐ |
| Listele lor nu au niciun produs comun (12 recomandări, cât arată pagina) | ✅ | ☐ |
| Maria: doar alergare, sub 300 lei; Radu: doar camping și drumeție | ✅ | ☐ |

Observație: listele rămân fără produse comune până la 25 de recomandări. Abia de la 30 apar produse comune, pentru că lista Mariei epuizează produsele de alergare sub 300 lei. Interfața cere 12, deci nu e o problemă.

### 5. Cazuri limită

| Verificare | API | Browser |
|---|---|---|
| Cont fără setări și fără istoric: rezervă cu cele mai cumpărate produse, marcată și cu motiv | ✅ | ☐ |
| E-mail deja folosit (și cu alte litere mari) → 409 „Există deja un cont cu acest e-mail.” | ✅ | ☐ |
| Parolă greșită → 401 „E-mail sau parolă greșită.” | ✅ | ☐ |
| Cumpărarea unui produs indisponibil → 409 „Produsul nu este disponibil.”; produs inexistent → 404 | ✅ | ☐ (butonul e dezactivat) |
| Niciun produs indisponibil nu apare în recomandări sau la produse similare | ✅ | ☐ |
| Buget sub prețul oricărui produs: rezervă goală, cu motiv | ✅ | ☐ |

## Probleme găsite

| Problemă | Task | Cine |
|---|---|---|
| Bugetul exclude toate produsele: pagina de recomandări spune „Îți arătăm cele mai cumpărate produse”, dar lista e goală | [CRI-31](https://linear.app/cristianstoian22/issue/CRI-31), rezolvat | Cristian |
| Setările spun că fără activitate nu există recomandări personalizate, dar backendul le face din nivel și stil | [CRI-29](https://linear.app/cristianstoian22/issue/CRI-29), rezolvat: textul din setări | Suhan |
| Prea puține produse de ciclism ultraușoare pentru nivelul intermediar (scenariul 1) | [CRI-30](https://linear.app/cristianstoian22/issue/CRI-30), rezolvat: 4 produse de ciclism Activ sunt acum ultraușoare | Suhan |

Niciuna nu blochează demonstrația: toate scenariile trec.

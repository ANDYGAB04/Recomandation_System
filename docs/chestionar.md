# Chestionarul pentru utilizatori

Evaluarea cu utilizatori reali, cerută în „Raportarea II”. Are două părți:

- **„Ți-a fost utilă?”**: votul Da / Nu de sub fiecare recomandare. Rezumatul e pe pagina **Evaluare**, la „Părerea utilizatorilor”.
- **Chestionarul**: 6 întrebări, completate în aplicație, pe pagina **Chestionar** (`/chestionar`).

## Formularul

Formularul e chiar în aplicație: **http://ADRESA:5173/chestionar**. `ADRESA` este adresa calculatorului pe care rulează aplicația.

- Se completează din contul participantului, o singură dată per cont.
- Răspunsurile sunt **anonime**:
  - nu se salvează numele, e-mailul sau contul;
  - doar o listă separată de conturi care au răspuns, ca nimeni să nu completeze de două ori;
  - răspunsurile nu au nicio legătură cu acea listă.
- Întrebările sunt definite într-un singur loc, `backend/app/survey.py`. Pagina și exportul CSV le citesc de acolo.

## Întrebările

Primele cinci sunt pe o scală de la 1 la 5, iar ultima e deschisă și opțională.

| # | Întrebare | 1 = | 5 = |
|---|---|---|---|
| q1 | Cât de potrivite au fost recomandările cu setările pe care le-ai ales? | Deloc potrivite | Foarte potrivite |
| q2 | Cât de clare au fost explicațiile de sub recomandări („Pentru că ai ales…”)? | Deloc clare | Foarte clare |
| q3 | După ce ți-ai schimbat setările, cât de bine s-a adaptat lista de recomandări? | Deloc | Foarte bine |
| q4 | Dacă magazinul ar fi real, cât de probabil ar fi să cumperi un produs recomandat? | Deloc probabil | Foarte probabil |
| q5 | Cât de ușor ți-a fost să folosești aplicația (cont, setări, recomandări)? | Foarte greu | Foarte ușor |
| q6 | Ce ți-a plăcut, ce ți-a lipsit sau ce ai schimba? | text liber | |

Fiecare întrebare verifică o parte a sistemului:

- **q1:** recomandarea pe baza profilului;
- **q2:** explicațiile;
- **q3:** reacția la schimbarea setărilor;
- **q4:** valoarea comercială;
- **q5:** interfața.

## Instrucțiunile pentru participanți

Textul de mai jos se trimite participanților, împreună cu linkul.

> Salut! Testăm **HobbyShop**, un magazin online demonstrativ care recomandă echipament de drumeție, camping, alergare și ciclism după preferințele tale. Durează aproximativ 10 minute. Toate produsele sunt fictive și nu se cumpără nimic pe bune.
>
> 1. Deschide **http://ADRESA:5173** și apasă **Înregistrare**. Creează un cont nou. Poți folosi orice adresă de e-mail, nu se verifică. Te rugăm să nu folosești o parolă pe care o mai ai și în altă parte.
> 2. Completează **Setările** după preferințele tale reale: activitățile pe care le practici, nivelul, stilul de echipament, sezonul și un buget. Apasă **Salvează setările**.
> 3. Deschide **Recomandări**. Citește explicațiile de sub produse și, la fiecare produs pe care îl parcurgi, răspunde la **„Ți-a fost utilă?”** cu Da sau Nu.
> 4. Schimbă o setare, de exemplu o activitate sau bugetul, și uită-te din nou la recomandări.
> 5. Opțional: deschide câteva produse, adaugă unul la favorite sau „cumpără-l” (simulat), apoi revino la recomandări.
> 6. Completează **Chestionarul**: linkul din bannerul de pe pagina Recomandări sau **http://ADRESA:5173/chestionar**. Răspunsurile sunt anonime.
>
> Mulțumim!

## Organizarea colectării (pasul 29)

### Pornirea aplicației pentru participanți

Aplicația rulează pe un calculator din aceeași rețea cu participanții, de exemplu laptopul nostru pe Wi-Fi-ul de acasă sau de la facultate.

**1. Adresa calculatorului în rețea.** Pe Windows, comanda `ipconfig` arată „IPv4 Address”, de exemplu `192.168.1.23`. Pe macOS și Linux, folosește `ip addr` sau `ifconfig`. În comenzile de mai jos, înlocuiește `ADRESA` cu ea.

**2. Datele.** Rulează **fără `--reset`**: `--reset` șterge conturile, voturile și răspunsurile participanților.

```bash
cd backend
python -m app.seed
```

**3. Backendul**, accesibil din rețea. CORS trebuie să accepte adresa frontendului:

```bash
cd backend
HOBBYSHOP_CORS_ORIGINS="http://ADRESA:5173,http://localhost:5173" uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Pe Windows, în PowerShell: `$env:HOBBYSHOP_CORS_ORIGINS="http://ADRESA:5173,http://localhost:5173"`, apoi comanda `uvicorn`.

**4. Frontendul**, accesibil din rețea, cu API-ul la adresa calculatorului:

```bash
cd frontend
VITE_API_URL=http://ADRESA:8000 npm run dev -- --host
```

Pe Windows, în PowerShell: `$env:VITE_API_URL="http://ADRESA:8000"`, apoi `npm run dev -- --host`.

**5. Verificarea.** De pe telefon, conectat la aceeași rețea, deschide `http://ADRESA:5173`. Indicatorul din bara de sus trebuie să arate „API conectat”. Dacă nu se deschide, permite în firewall-ul Windows conexiunile către porturile 5173 și 8000.

### Lista de verificare

- [ ] Aplicația pornită ca mai sus și verificată de pe un alt dispozitiv.
- [ ] Instrucțiunile și linkul trimise de amândoi (Suhan coordonează).
- [ ] Cel puțin **8 participanți** au completat chestionarul. Numărul de răspunsuri reale apare în `GET /survey` (câmpul `responses`; datele de test sunt numărate separat, în `test_responses`).
- [ ] Voturile „Ți-a fost utilă?” apar pe pagina Evaluare, la „Părerea utilizatorilor”.
- [ ] Răspunsurile exportate în `docs/chestionar-raspunsuri.csv` (vezi mai jos) și adăugate în repository.
- [ ] Baza de date folosită (`backend/data/hobbyshop.db`) păstrată pentru analiza de la pasul 30, **fără `--reset`**.

### Exportul răspunsurilor

```bash
cd backend
python -m app.survey_export          # scrie docs/chestionar-raspunsuri.csv
```

Fișierul are o linie pe răspuns: `raspuns`, `sursa` (`real` sau `date de test`), `data` (doar ziua), `q1`–`q5`, `q6`. Nu conține date personale. Comanda afișează câte răspunsuri sunt reale și câte de test și media fiecărei întrebări pe scală, separat pentru fiecare.

### Datele de test

Ca paginile să nu fie goale înainte de colectare, `python -m app.seed` adaugă și **date de test**, generate automat, nu de persoane reale:

- 12 răspunsuri la chestionar, salvate cu `is_test_data = true`. Comentariile care nu sunt goale încep cu „[date de test]”.
- câte 5 voturi „Ți-a fost utilă?” pentru primii 12 clienți simulați, pe recomandările calculate pentru ei. Votul „util” e mai probabil când scorul recomandării e mai mare.

Datele de test sunt numărate separat peste tot: în `GET /survey` (`test_responses`), în `GET /evaluation/feedback` (`test_data`), în export (coloana `sursa`) și pe pagina Evaluare, unde au eticheta „Date de test”. **Nu le prezentăm ca rezultate ale evaluării cu utilizatori.** Scriptul le adaugă o singură dată; rularea repetată nu le dublează.

## Rezultate (pasul 30)

**Participanți reali: 0.** Colectarea cu utilizatori reali nu a avut loc, așa că nu avem rezultate ale evaluării cu utilizatori. Tot ce urmează sunt **date de test**, generate de `python -m app.seed`. Ele arată doar că instrumentele funcționează de la un capăt la altul: chestionarul, voturile, exportul și calculele.

### Chestionarul (date de test)

12 răspunsuri de test, din `docs/chestionar-raspunsuri.csv` (`sursa = date de test`):

| # | Ce verifică | Media (1–5) |
|---|---|---|
| q1 | Potrivirea cu setările | 4,17 |
| q2 | Claritatea explicațiilor | 3,92 |
| q3 | Adaptarea la schimbarea setărilor | 3,58 |
| q4 | Intenția de cumpărare | 4,08 |
| q5 | Ușurința de folosire | 3,50 |

Răspunsurile de test sunt alese aleatoriu din {2, 3, 4, 4, 5, 5}. Diferențele dintre întrebări nu spun nimic despre aplicație.

La q6, 9 răspunsuri de test au comentariu și 3 sunt goale. Sunt 3 comentarii diferite (despre explicații, buget și filtre), repetate, și toate încep cu „[date de test]”.

### „Ți-a fost utilă?” (date de test)

Din `GET /evaluation/feedback`, câmpul `test_data`:

| Recomandări | Voturi | Utile |
|---|---|---|
| Toate | 60 (12 clienți simulați) | 51 (85%) |
| Personalizate | 60 | 51 (85%) |
| Rezervă (popularitate) | 0 | – |

Voturile de test sunt date pe recomandările calculate chiar de aplicație. Un vot „util” e mai probabil când scorul recomandării e mai mare (probabilitate 0,45 + 0,5 × scor). Procentul depinde deci de această regulă, nu de părerea cuiva. Clienții simulați au istoric, așa că primesc recomandări personalizate; de aceea rezerva nu are voturi.

### Ce înseamnă

- Evaluarea cu utilizatori nu confirmă și nu infirmă metoda: nu avem păreri reale. Singura evaluare cu rezultate este cea **offline** (README, „Evaluarea offline”): Recall@5 0,304 față de 0,164 la popularitate, pe date sintetice.
- Instrumentul e gata. Cu cel puțin 8 participanți reali, comenzile de mai sus (`python -m app.survey_export` și pagina Evaluare) dau rezultatele reale, separat de datele de test. Tabelele de aici se refac atunci cu cifrele reale.

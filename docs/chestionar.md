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
- [ ] Cel puțin **8 participanți** au completat chestionarul. Numărul de răspunsuri apare în `GET /survey` (câmpul `responses`).
- [ ] Voturile „Ți-a fost utilă?” apar pe pagina Evaluare, la „Părerea utilizatorilor”.
- [ ] Răspunsurile exportate în `docs/chestionar-raspunsuri.csv` (vezi mai jos) și adăugate în repository.
- [ ] Baza de date folosită (`backend/data/hobbyshop.db`) păstrată pentru analiza de la pasul 30, **fără `--reset`**.

### Exportul răspunsurilor

```bash
cd backend
python -m app.survey_export          # scrie docs/chestionar-raspunsuri.csv
```

Fișierul are o linie pe răspuns: `raspuns`, `data` (doar ziua), `q1`–`q5`, `q6`. Nu conține date personale. Comanda afișează și media fiecărei întrebări pe scală.

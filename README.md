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

Pașii de instalare și pornire se adaugă odată cu scheletele aplicației:

- backend: pasul 02 (CRI-6);
- frontend: pasul 03 (CRI-7).

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


Sennik-App - README
====================

Opis projektu
-------------
Sennik-App to aplikacja backendowa służąca do monitorowania snu i samopoczucia użytkownika.
Wykorzystuje FastAPI, PostgreSQL, SQLModel oraz Alembic.

Instrukcja uruchamiania
-----------------------

1. Sklonuj repozytorium:
   git clone <URL_DO_REPO>
   cd sennik-app

2. Stwórz i aktywuj środowisko wirtualne:
   Windows:
     python -m venv venv
     .\venv\Scripts\Activate.ps1
   Linux/Mac:
     python3 -m venv venv
     source venv/bin/activate

3. Zainstaluj zależności:
   cd backend
   pip install -r requirements.txt

4. Skonfiguruj PostgreSQL:
   CREATE USER sennik_user WITH PASSWORD 'twoje_haslo';
   CREATE DATABASE sennik_db OWNER sennik_user;
   GRANT ALL PRIVILEGES ON DATABASE sennik_db TO sennik_user;

5. Utwórz plik .env w głównym katalogu:
   ENVIRONMENT=dev
   DEBUG=True
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=sennik_db
   DB_USER=sennik_user
   DB_PASSWORD=twoje_haslo
   JWT_SECRET=sekretnyklucz
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60

6. Uruchom migracje:
   alembic upgrade head

7. Uruchom backend:
   uvicorn backend.main:app --reload

8. Uruchom frontend (Vite):
   cd ..\frontend
   npm install
   npm run dev

## 🧾 Najważniejsze komendy (z opisami)

### 🔹 Backend (Uvicorn)

**uvicorn backend.main:app --reload**  
– uruchamia backend FastAPI z automatycznym przeładowaniem przy zmianach w kodzie.

---

### Frontend (Vite)

**npm install**  
- instaluje zaleznosci frontendu.

**npm run dev**  
- uruchamia serwer developerski Vite (zwykle http://localhost:5173).

---

### 🔹 Alembic (migracje)

**alembic revision --autogenerate -m "opis zmian"**  
– tworzy nowy plik migracji na podstawie różnic w modelach SQLModel.

**alembic upgrade head**  
– stosuje wszystkie migracje do najnowszej wersji i aktualizuje schemat bazy.

**alembic downgrade -1**  
– cofa bazę danych o jedną migrację wstecz.

---

### 🔹 Git

**git status**  
– pokazuje zmiany w repozytorium (nowe, zmodyfikowane, usunięte pliki).

**git add .**  
– dodaje wszystkie zmienione pliki do najbliższego commita.

**git commit -m "opis zmian"**  
– zapisuje zatwierdzone zmiany w repo jako nowy commit.

**git push origin main**  
– wysyła commit(y) z lokalnego repo na zdalne repozytorium (gałąź `main`).

**git checkout -b feature/nazwa-funkcji**  
– tworzy nowy branch i jednocześnie na niego przełącza, np. na nową funkcjonalność.

Seedowanie danych testowych
---------------------------

Projekt zawiera lokalny seeder generujący przykładowych użytkowników oraz historię wpisów `DailyLog`.

Seeder jest przeznaczony tylko do środowiska developerskiego/testowego. Przed uruchomieniem upewnij się, że w pliku `backend/.env` masz:

   ENVIRONMENT=dev

Profile użytkowników znajdują się w katalogu:

   scripts/synthetic_data/profiles/

Każdy plik `.json` w tym katalogu opisuje jednego testowego użytkownika, np.:

   scripts/synthetic_data/profiles/example.json

Aby uruchomić seeder, przejdź do głównego katalogu projektu i wykonaj:

   .\venv\Scripts\Activate.ps1
   python -m scripts.synthetic_data.seed

Seeder:

- wczytuje wszystkie profile `.json` z katalogu `profiles`,
- tworzy użytkownika w tabeli `users`,
- hashuje hasło tym samym mechanizmem co zwykła rejestracja,
- generuje historyczne wpisy `DailyLog`,
- wylicza `sleep_duration` i `day_score`,
- pomija użytkownika, jeśli konto z takim adresem e-mail już istnieje.

Po poprawnym uruchomieniu można zalogować się na konto testowe danymi z profilu, np.:

   student.test@example.com
   Test123!
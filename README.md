# 🚗 RideWMy – Olcsó és kényelmes utazás Erdélyben

A **RideWMy** egy Flask-alapú, modern telekocsi webalkalmazás, amely megkönnyíti az erdélyi városok közötti utazást. Az alkalmazás Figma dizájn alapján készült, interaktív térképes keresővel, automata útvonal- és menetidő-kalkulációval, valamint dinamikus foglalási rendszerrel rendelkezik.

---

## ✨ Főbb funkciók

- 🏠 **Főoldal (`/`)**:
  - Figma-alapú, letisztult kezdőlap keresősávval.
  - **Közelgő népszerű utazások**: 3 véletlenszerűen kiválasztott, szabad hellyel rendelkező út megjelenítése dinamikus középre igazítással.
  - Automatikus település-autokiegészítés (Nominatim API + erdélyi gyorsítótár).

- 🗺️ **Interaktív kereső és szűrő (`/search`)**:
  - Térképes megjelenítés Leaflet.js segítségével.
  - Egyedi magasságméretezés (átméretezhető és összecsukható térkép).
  - Élő menetidő-, távolság- és érkezési idő kalkuláció az OSRM API használatával.
  - Szűrés indulás, érkezés, dátum és szabad helyek száma szerint.
  - **Intelligens szűrés**: A betelt utak (`available_seats == 0`) automatikusan elrejtőznek a keresőből és a főoldalról, de az adatbázisban megmaradnak.

- 🚘 **Utazás részletei & Foglalás (`/ride/<trip_id>`)**:
  - Részletes idővonal grid elrendezésben (pontos indulási és érkezési idő pontelcsúszás nélkül).
  - Sofőr adatai, értékelések, gépjármű leírása és utazási feltételek (nem dohányzó, csomagméret).
  - Térképes útvonal előnézet.
  - **Dinamikus árkalkulátor**: Kiválasztott helyek számának megfelelően azonnali összegszámítás.
  - Betelt utak esetén automatikus **„Betelt”** státusz jelzése és a foglalás letiltása.

- ➕ **Út meghirdetése (`/create-ride`)**:
  - Meglévő jármű kiválasztása vagy új autó hozzáadása egyéni adatokkal (márka, modell, szín, rendszám).
  - Térképes útvonal előnézet a pontok megadásakor.
  - Szigorú dátumkezelés: a múltbéli dátumok tiltva vannak (`minDate: "today"`), és a rendszer nem enged dátum nélkül hirdetést feladni.

- ⭐ **Értékelések (`/reviews`)**:
  - Interaktív, csillagos értékelő rendszer a lezajlott utazásokhoz.

---

## 🛠️ Technológiai stakk

### Backend
- **Python 3.x** & **Flask**
- **Flask-SQLAlchemy** (ORM adatbázis-kezelés)
- **PyMySQL** / **MySQL** (XAMPP környezet)

### Frontend
- **HTML5**, **CSS3**, **JavaScript (ES6)**
- **Bootstrap 5.3** & **Bootstrap Icons**
- **Google Fonts** (*Bagel Fat One*, *Poppins*)
- **Leaflet.js** (OpenStreetMap csempékkel)
- **Flatpickr** (Interaktív, magyar nyelvű dátum- és időválasztó)

### Külső API-k & Szolgáltatások
- **OSRM (Open Source Routing Machine)** – Autós útvonaltervezés, távolság és menetidő számítás.
- **Nominatim OpenStreetMap** – Geokódolás és dinamikus város autokiegészítés.

---

## 🚀 Telepítés és futtatás

### 1. Repozitórium klónozása
```bash
git clone https://github.com/inczemihaly-rgb/RideWMy.git
cd RideWMy

# 🚗 RideWMy – Olcsó és kényelmes utazás Erdélyben

A **RideWMy** egy Flask-alapú, modern telekocsi webalkalmazás, amely megkönnyíti az erdélyi városok közötti utazást. Az alkalmazás Figma dizájn alapján készült, interaktív térképes keresővel, automata útvonal- és menetidő-kalkulációval, teljes körű profil- és hirdetéskezeléssel, valamint dinamikus foglalási és értesítési rendszerrel rendelkezik.

---

## ✨ Főbb funkciók

- 🏠 **Főoldal (`/`)**:
  - Figma-alapú, letisztult kezdőlap gyorskereső sávval.
  - **Közelgő népszerű utazások**: 3 véletlenszerűen kiválasztott, szabad hellyel rendelkező út megjelenítése egységesített kártyamagassággal (hosszú helyszínnevek esetén sem csúsznak el az árak és a gombok).
  - Automatikus település-autokiegészítés (Photon API + Nominatim API + erdélyi gyorsítótár).

- 🗺️ **Interaktív kereső és szűrő (`/search`)**:
  - Térképes megjelenítés Leaflet.js segítségével, csoportosított indulási jelölőkkel és útvonal-előnézettel.
  - Egyedi magasságméretezés (húzható fogantyúval átméretezhető és egy kattintással nagyítható/kicsinyíthető térkép).
  - Élő menetidő-, távolság- és érkezési idő kalkuláció az OSRM API használatával.
  - Szűrés indulás, érkezés, dátum és szabad helyek száma szerint.
  - **Intelligens szűrés és saját utak kezelése**: A betelt utak (`available_seats == 0`) automatikusan elrejtőznek a keresőből és a főoldalról; a felhasználó saját hirdetéseinél pedig *„Foglalás”* helyett *„Részletek”* gomb jelenik meg.

- 🚘 **Utazás részletei & Foglalás (`/ride/<trip_id>`)**:
  - Részletes idővonal pontos indulási és érkezési időkkel, útvonal-előnézeti térképpel.
  - Sofőr adatai, értékelések, gépjármű leírása és utazási feltételek (nem dohányzó, csomagméret).
  - **Dinamikus árkalkulátor**: A kiválasztott helyek számának megfelelően azonnali összegszámítás.
  - Betelt utak esetén automatikus **„Betelt”** státusz jelzése és a foglalás letiltása, saját hirdetés megnyitásakor pedig közvetlen átirányítás a szerkesztőfelületre.

- ➕ **Út meghirdetése (`/create-ride`)**:
  - Meglévő jármű kiválasztása vagy új autó hozzáadása egyéni adatokkal (márka, modell, szín, rendszám).
  - Térképes útvonal előnézet és menetidő-számítás a pontok megadásakor.
  - Szigorú dátumkezelés: a múltbéli dátumok tiltva vannak (`minDate: "today"`), és a rendszer nem enged dátum nélkül hirdetést feladni.

- 👤 **Saját profil & Gyors jóváhagyás (`/profile`)**:
  - Felhasználói adatok (név, e-mail, telefonszám, értékelési átlag) és elsődleges autó adatainak megjelenítése.
  - **Profil szerkesztése és törlése**: Modális ablakon keresztül módosítható a név, telefonszám és autóadatok, valamint véglegesen törölhető a felhasználói fiók.
  - **Gyors jóváhagyás**: Ha egy meghirdetett útra új jelentkező érkezett, az *Utazásaim* fülek fölött automatikusan megjelenik a **Beérkezett jelentkezések** doboz, ahol egyetlen kattintással elfogadható vagy elutasítható a foglalás (ha nincs függőben lévő jelentkezés, a doboz rejtve marad).
  - **Utazásaim fülek**: Átlátható bontás *Közelgő utak*, *Korábbi utak* és *Meghirdetett utak* között (a jelentkezésekkel rendelkező saját hirdetések automatikusan előre sorolódnak).

- ⚙️ **Saját utazás kezelése (`/manage-ride/<trip_id>`)**:
  - Meghirdetett utazás adatainak módosítása (indulási/érkezési helyszín autokiegészítéssel, dátum és időpont, szabad helyek száma, ár/fő) élő OSRM térképes útvonal-frissítéssel.
  - Meghirdetett utazás törlése megerősítő modállal.
  - Jelentkező utasok kezelése (elfogadás / elutasítás), valamint a megerősített utasok kapcsolattartási telefonszámának megjelenítése.

- 🔔 **Értesítési rendszer & Autentikáció (`/login`, `/register`)**:
  - Globális értesítő jelvény a felső navigációs sávban (`X jelentkező` csengő ikonnal) és a profil menüben minden oldalon, ha jóváhagyásra váró foglalási igény érkezett.
  - Munkamenet-alapú regisztráció, bejelentkezés és kijelentkezés.

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
- **Photon API (`photon.komoot.io`)** – Gyors, valós idejű település-autokiegészítés.
- **Nominatim OpenStreetMap** – Geokódolás és koordináták feloldása.

---

## 🚀 Telepítés és futtatás

### 1. Repozitórium klónozása
```bash
git clone [https://github.com/inczemihaly-rgb/RideWMy.git](https://github.com/inczemihaly-rgb/RideWMy.git)
cd RideWMy
```

### 2. Virtuális környezet és függőségek telepítése
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

pip install flask flask-sqlalchemy pymysql werkzeug
```

### 3. Adatbázis beállítása (XAMPP)
1. Indítsd el a XAMPP vezérlőpultban az **Apache** és a **MySQL** szolgáltatásokat.
2. Nyisd meg a **phpMyAdmin** felületet (`http://localhost/phpmyadmin`), és hozz létre egy új adatbázist `ridewmy` néven (`utf8mb4_general_ci` karakterkódolással).
3. Az alkalmazás első indításkor automatikusan létrehozza a szükséges táblákat (`db.create_all()`).

### 4. Alkalmazás indítása
```bash
python app.py
```
Ezután az alkalmazás elérhető a böngészőben a **`http://127.0.0.1:5000`** címen.
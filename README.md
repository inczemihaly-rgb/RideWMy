<div align="center">

# 🚗 RideWMy
### Olcsó és kényelmes telekocsi-megoldás Erdélyben

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-000000?style=for-the-badge&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-XAMPP-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![Leaflet](https://img.shields.io/badge/Leaflet-OpenStreetMap-199900?style=for-the-badge&logo=leaflet&logoColor=white)

<p align="center">
  <a href="#-főbb-funkciók">Főbb funkciók</a> •
  <a href="#-oldalak-és-végpontok">Oldalak</a> •
  <a href="#️-technológiai-stakk">Technológiák</a> •
  <a href="#-projekt-felépítése">Projekt felépítése</a> •
  <a href="#-telepítés-és-futtatás">Telepítés</a>
</p>

</div>

---

## 📖 Áttekintés

A **RideWMy** egy Flask-alapú, modern telekocsi webalkalmazás, amely az erdélyi városok közötti utazást teszi gyorsabbá, olcsóbbá és átláthatóbbá. Az alkalmazás Figma dizájn alapján készült, és valós idejű térképes útvonaltervezéssel, automata menetidő-kalkulációval, teljes körű sofőr- és utasoldali kezelőfelülettel, valamint azonnali jelentkezési értesítésekkel működik.

---

## ✨ Főbb funkciók

### 🧭 Utazáskeresés és térképes tervezés
* **Gyorskereső és kiemelt utak (`/`)**: Letisztult kezdőlap gyors település-autokiegészítéssel, valamint 3 véletlenszerűen ajánlott, szabad hellyel rendelkező úttal — egységes kártyamagassággal hosszú helyszínnevek esetén is.
* **Interaktív térképes kereső (`/search`)**: Leaflet.js térkép csoportosított indulási jelölőkkel, húzható magasságállítással és egykattintásos nagyítással.
* **Élő OSRM kalkuláció**: Automatikus útvonalrajzolás, távolság-, menetidő- és várható érkezési idő számítás.
* **Intelligens szűrés**: Szűrés indulási/érkezési város, dátum és szabad helyek száma alapján. A betelt utak (`0 szabad hely`) automatikusan rejtve maradnak a listákban, a saját hirdetéseknél pedig *„Részletek”* gomb jelenik meg.

### 🚘 Foglalás és hirdetésfeladás
* **Részletes útvonalnézet (`/ride/<id>`)**: Idővonal pontos indulási és érkezési adatokkal, térképes előnézettel, járműadatokkal, utazási feltételekkel és **dinamikus árkalkulátorral**.
* **Új út meghirdetése (`/create-ride`)**: Meglévő saját autó kiválasztása vagy új jármű rögzítése, élő útvonal-előnézettel és múltbéli dátumok tiltásával (`minDate: "today"`).

### 👤 Profil, hirdetéskezelés és értesítések
* **Globális értesítési jelvény**: Ha bármelyik meghirdetett útra új jelentkezés érkezett, minden oldal felső navigációs sávjában megjelenik egy figyelmeztető jelvény (`X jelentkező`).
* **Saját profil és gyors jóváhagyás (`/profile`)**: Személyes és autóadatok szerkesztése vagy törlése, fülekre bontott utazáslista (*Közelgő*, *Korábbi*, *Meghirdetett utak*), valamint **azonnali elfogadás/elutasítás** közvetlenül a profiloldalról.
* **Utazás szerkesztése (`/manage-ride/<id>`)**: Meghirdetett utak adatainak módosítása élő térképes frissítéssel, út törlése, jelentkező utasok elbírálása és a megerősített utasok telefonszámának megtekintése.
* **Értékelési rendszer (`/reviews`)**: Csillagos értékelés és szöveges visszajelzés a lezajlott utazások után.

---

## 🗺️ Oldalak és végpontok

| Útvonal | Sablon | Leírás |
| :--- | :--- | :--- |
| `/` vagy `/home` | `home.html` | Kezdőlap gyorskeresővel és kiemelt utakkal |
| `/search` | `index.html` | Interaktív térképes kereső és szűrőfelület |
| `/ride/<trip_id>` | `ride_details.html` | Utazás részletei, árkalkulátor és helyfoglalás |
| `/create-ride` | `create_ride.html` | Új utazás és jármű meghirdetése |
| `/profile` | `profile.html` | Saját profil, utazások áttekintése és gyors jóváhagyás |
| `/manage-ride/<trip_id>` | `manage_ride.html` | Saját hirdetés szerkesztése és utasok kezelése |
| `/reviews` | `reviews.html` | Sofőrök és utazások értékelése |
| `/login`, `/register` | `login.html`, `register.html` | Bejelentkezés és regisztráció |

---

## 🛠️ Technológiai stakk

| Réteg | Technológiák és szolgáltatások |
| :--- | :--- |
| **Backend** | Python 3.x, Flask, Flask-SQLAlchemy, PyMySQL, Werkzeug |
| **Adatbázis** | MySQL (XAMPP környezet) |
| **Frontend** | HTML5, CSS3, JavaScript (ES6), Bootstrap 5.3, Bootstrap Icons |
| **Tipográfia & UI** | Google Fonts (*Bagel Fat One*, *Poppins*), Flatpickr (magyar lokalizációval) |
| **Térkép & API-k** | Leaflet.js (OpenStreetMap), OSRM Routing API, Photon API, Nominatim API |

---

## 📂 Projekt felépítése

```text
RideWMy/
├── app.py                  # Flask alkalmazás, útvonalak és üzleti logika
├── models.py               # SQLAlchemy adatbázis-modellek (User, Car, Trip, Booking, Review)
├── README.md               # Projekt dokumentáció
└── templates/
    ├── home.html           # Főoldal
    ├── index.html          # Térképes kereső
    ├── ride_details.html   # Utazás részletei és foglalás
    ├── create_ride.html    # Út meghirdetése
    ├── profile.html        # Saját profil és gyors jóváhagyás
    ├── manage_ride.html    # Meghirdetett út kezelése
    ├── reviews.html        # Értékelések
    ├── login.html          # Bejelentkezés
    └── register.html       # Regisztráció
```

---

## 🚀 Telepítés és futtatás

### 1. Repozitórium klónozása
```bash
git clone [https://github.com/inczemihaly-rgb/RideWMy.git](https://github.com/inczemihaly-rgb/RideWMy.git)
cd RideWMy
```

### 2. Virtuális környezet és csomagok telepítése
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux / macOS:
source venv/bin/activate

pip install flask flask-sqlalchemy pymysql werkzeug
```

### 3. Adatbázis létrehozása (XAMPP)
1. Indítsd el a XAMPP vezérlőpultban az **Apache** és a **MySQL** modulokat.
2. Nyisd meg a **phpMyAdmin** felületet (`http://localhost/phpmyadmin`), és hozz létre egy új adatbázist `ridewmy` néven (`utf8mb4_general_ci` karakterkódolással).

> **Megjegyzés:** Az alkalmazás az első indításkor automatikusan létrehozza az összes szükséges táblát a `db.create_all()` segítségével.

### 4. Szerver indítása
```bash
python app.py
```
Az alkalmazás ezt követően elérhető a böngészőben a **`http://127.0.0.1:5000`** címen.
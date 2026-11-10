from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User, Car, Trip, Booking, Review

app = Flask(__name__)

# XAMPP MySQL kapcsolódás (root user, jelszó nélkül, localhost, ridewmy adatbázis)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ridewmy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ez a titkos kulcs kell a session (munkamenet) biztonságos működéséhez!
app.secret_key = 'ridewmy_super_secret_key_123'

# SQLAlchemy inicializálása
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    # Lekérjük az adatbázisban lévő összes utat
    trips_from_db = Trip.query.all()
    
    rides_data = []
    for trip in trips_from_db:
        rides_data.append({
            "id": trip.trip_id,
            "driver": trip.driver.full_name if trip.driver else "Ismeretlen",
            "rating": "5.0",
            "from": "Kiindulás",
            "to": "Úticél",
            "fromLat": float(trip.start_latitude) if trip.start_latitude else None,
            "fromLng": float(trip.start_longitude) if trip.start_longitude else None,
            "toLat": float(trip.destination_latitude) if trip.destination_latitude else None,
            "toLng": float(trip.destination_longitude) if trip.destination_longitude else None,
            "price": f"{trip.price_per_seat} RON",
            "seats": f"{trip.available_seats} szabad hely",
            "startTime": trip.departure_time.strftime('%H:%M') if trip.departure_time else "08:00",
            "endTime": trip.estimated_arival_time.strftime('%H:%M') if trip.estimated_arival_time else "10:00"
        })

    return render_template('index.html', rides=rides_data)

#       BEJELENTKEZÉS (LOGIN) VÉGPONT
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Felhasználó keresése email alapján
        user = User.query.filter_by(email=email).first()
        
        # Jelszó ellenőrzése a modell beépített check_password metódusával
        if user and user.check_password(password):
            # SIKERES BEJELENTKEZÉS: Munkamenet (session) adatok beállítása
            session['user_id'] = user.user_id
            session['user_name'] = user.full_name
            
            print(f"Sikeres bejelentkezés: {user.full_name}")
            return redirect(url_for('index')) # Sikeres login után visszairányít a főoldalra
        else:
            return "Hiba: Hibás email cím vagy jelszó!", 401

    return "Itt lesz a bejelentkezési űrlap (GET kérés)."

#       ÚJ: KIJELENTKEZÉS (LOGOUT) VÉGPONT
@app.route('/logout')
def logout():
    # Töröljük a session-ből a felhasználói adatokat
    session.pop('user_id', None)
    session.pop('user_name', None)
    
    print("Sikeres kijelentkezés!")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
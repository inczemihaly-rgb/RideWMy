import random
from datetime import datetime
import json
import urllib.parse
import urllib.request
from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User, Car, Trip, Booking, Review

app = Flask(__name__)
app.secret_key = 'ridewmy_super_secret_key'

# XAMPP MySQL kapcsolódás
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ridewmy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

CITY_COORDS = {
    "marosvásárhely": (46.5425, 24.5575),
    "kolozsvár": (46.7712, 23.6236),
    "brassó": (45.6579, 25.6012),
    "sepsiszentgyörgy": (45.8636, 25.7878),
    "székelyudvarhely": (46.3053, 25.2936),
    "csíkszereda": (46.3606, 25.8016),
    "nagyszeben": (45.7983, 24.1256),
    "barót": (46.0747, 25.6025),
    "farkaslaka": (46.3811, 25.2153),
    "kézdivásárhely": (46.0000, 26.1383),
    "gyergyószentmiklós": (46.7225, 25.6006)
}

def get_city_coordinates(city_name):
    if not city_name:
        return 46.5425, 24.5575
    norm = city_name.strip().lower()
    if norm in CITY_COORDS:
        return CITY_COORDS[norm]
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={urllib.parse.quote(city_name)}&countrycodes=ro&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'RideWmyApp/1.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception:
        pass
    return 46.5425, 24.5575

def get_rides_data_list(trips):
    rides_data = []
    for trip in trips:
        driver_name = trip.driver.full_name if hasattr(trip.driver, 'full_name') else getattr(trip.driver, 'name', 'Ismeretlen')
        rides_data.append({
            "id": trip.trip_id,
            "driver": driver_name,
            "rating": "5.0",
            "from": trip.start_city if trip.start_city else "Kiindulás",
            "to": trip.destination_city if trip.destination_city else "Úticél",
            "fromLat": float(trip.start_latitude) if trip.start_latitude else 46.5425,
            "fromLng": float(trip.start_longitude) if trip.start_longitude else 24.5575,
            "toLat": float(trip.destination_latitude) if trip.destination_latitude else 46.7712,
            "toLng": float(trip.destination_longitude) if trip.destination_longitude else 23.6236,
            "price": f"{trip.price_per_seat:.2f} RON",
            "seats": f"{trip.available_seats} szabad hely",
            "startTime": trip.departure_time.strftime('%Y. %m. %d.') if trip.departure_time else "2026. 10. 25.",
            "startHour": trip.departure_time.strftime('%H:%M') if trip.departure_time else "08:00",
            "endTime": trip.estimated_arival_time.strftime('%H:%M') if trip.estimated_arival_time else "10:00",
            "duration": "2 óra 15 perc",
            "distance": "105 km",
            "car": f"{trip.car.brand} {trip.car.model}" if trip.car else "Volkswagen Golf"
        })
    return rides_data

# --- FŐOLDAL ---
@app.route('/')
@app.route('/home')
def home():
    trips_from_db = Trip.query.filter(Trip.available_seats > 0).all()
    rides_data = get_rides_data_list(trips_from_db)
    random_rides = random.sample(rides_data, min(len(rides_data), 3)) if rides_data else []
    return render_template('home.html', rides=random_rides)

# --- UTAK KERESÉSE ---
@app.route('/search')
def search():
    from_query = request.args.get('from', '').strip()
    to_query = request.args.get('to', '').strip()
    date_query = request.args.get('date', '').strip()
    seats_query = request.args.get('seats', '').strip()
    
    query = Trip.query.filter(Trip.available_seats > 0)
    
    if from_query:
        query = query.filter(Trip.start_city.ilike(f"%{from_query}%"))
    if to_query:
        query = query.filter(Trip.destination_city.ilike(f"%{to_query}%"))
    if date_query:
        query = query.filter(db.func.date(Trip.departure_time) == date_query)
    if seats_query and seats_query.isdigit():
        query = query.filter(Trip.available_seats >= int(seats_query))
        
    trips_from_db = query.all()
    rides_data = get_rides_data_list(trips_from_db)
    return render_template('index.html', rides=rides_data)

# --- ÉRTÉKELÉSEK ---
@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    if 'user_id' not in session:
        flash("Értékelés írásához kérjük, jelentkezz be!", "warning")
        return redirect(url_for('login'))
        
    current_user_id = session['user_id']
    
    if request.method == 'POST':
        trip_id = request.form.get('trip_id')
        rating = request.form.get('rating', 5)
        comment = request.form.get('comment', '')
        
        booking = Booking.query.filter_by(trip_id=trip_id, pasinger_id=current_user_id).first()
        
        if not booking:
            booking = Booking(trip_id=trip_id, pasinger_id=current_user_id, seats_bookd=1, booking_status=True)
            db.session.add(booking)
            db.session.commit()
            
        new_review = Review(
            booking_id=booking.booking_id,
            reviewer_id=current_user_id,
            rating=int(rating),
            comment=comment
        )
        db.session.add(new_review)
        db.session.commit()
        flash("Köszönjük az értékelést!", "success")
        return redirect(url_for('home'))

    user_bookings = Booking.query.filter_by(pasinger_id=current_user_id).all()
    trips_to_review = []
    
    if user_bookings:
        for b in user_bookings:
            if b.trip:
                driver_name = b.trip.driver.full_name if hasattr(b.trip.driver, 'full_name') else getattr(b.trip.driver, 'name', 'Sofőr')
                trips_to_review.append({
                    "trip_id": b.trip.trip_id,
                    "label": f"{b.trip.start_city} → {b.trip.destination_city} ({driver_name})"
                })
    else:
        all_trips = Trip.query.all()
        for t in all_trips:
            driver_name = t.driver.full_name if hasattr(t.driver, 'full_name') else getattr(t.driver, 'name', 'Sofőr')
            trips_to_review.append({
                "trip_id": t.trip_id,
                "label": f"{t.start_city} → {t.destination_city} ({driver_name})"
            })

    return render_template('reviews.html', trips=trips_to_review)

# --- UTAZÁS RÉSZLETEI ---
@app.route('/ride/<int:trip_id>')
def ride_details(trip_id):
    trip = db.session.get(Trip, trip_id)
    if not trip:
        return redirect(url_for('search'))

    formatted_date = trip.departure_time.strftime('%Y. %B %d.').lower() if trip.departure_time else "2026. október 25."
    start_hour = trip.departure_time.strftime('%H:%M') if trip.departure_time else "08:00"
    end_hour = trip.estimated_arival_time.strftime('%H:%M') if trip.estimated_arival_time else "10:15"

    car_name = f"{trip.car.brand} {trip.car.model} - {trip.car.color}" if trip.car else "Volkswagen Passat - Ezüst"
    driver_name = trip.driver.full_name if hasattr(trip.driver, 'full_name') else getattr(trip.driver, 'name', 'Sofőr')

    ride_detail = {
        "id": trip.trip_id,
        "driver_name": driver_name,
        "rating": "5.0",
        "date_formatted": formatted_date,
        "from": trip.start_city if trip.start_city else "Kiindulás",
        "to": trip.destination_city if trip.destination_city else "Úticél",
        "from_lat": float(trip.start_latitude) if trip.start_latitude else 46.5425,
        "from_lng": float(trip.start_longitude) if trip.start_longitude else 24.5575,
        "to_lat": float(trip.destination_latitude) if trip.destination_latitude else 46.7712,
        "to_lng": float(trip.destination_longitude) if trip.destination_longitude else 23.6236,
        "start_hour": start_hour,
        "end_hour": end_hour,
        "duration": "2 óra 15 perc",
        "car": car_name,
        "price_num": int(trip.price_per_seat),
        "available_seats": trip.available_seats
    }

    return render_template('ride_details.html', ride=ride_detail)

# --- FOGLALÁS VÉGREHAJTÁSA ---
@app.route('/book-ride', methods=['POST'])
def book_ride():
    if 'user_id' not in session:
        flash("Foglaláshoz kérjük, jelentkezz be!", "warning")
        return redirect(url_for('login'))

    trip_id = int(request.form.get('trip_id'))
    seats_requested = int(request.form.get('seats', 1))
    passenger_id = session['user_id']

    trip = db.session.get(Trip, trip_id)
    if trip and trip.available_seats >= seats_requested:
        trip.available_seats -= seats_requested
        booking = Booking(
            trip_id=trip.trip_id,
            pasinger_id=passenger_id,
            seats_bookd=seats_requested,
            booking_status=True
        )
        db.session.add(booking)
        db.session.commit()
        flash("Sikeres foglalás!", "success")
    
    return redirect(url_for('ride_details', trip_id=trip_id))

# --- ÚT MEGHIRDETÉSE ---
@app.route('/create-ride', methods=['GET', 'POST'])
def create_ride():
    if 'user_id' not in session:
        flash("Út meghirdetéséhez kérjük, jelentkezz be!", "warning")
        return redirect(url_for('login'))

    current_user_id = session['user_id']
    # Kizárólag a bejelentkezett felhasználó saját autóit kérjük le
    user_cars = Car.query.filter_by(owner_id=current_user_id).all()

    if request.method == 'POST':
        from_city = request.form.get('from', 'Marosvásárhely').strip()
        to_city = request.form.get('to', 'Kolozsvár').strip()
        departure_time_str = request.form.get('datetime')
        seats = request.form.get('seats')
        price = request.form.get('price')
        car_option = request.form.get('car_id')

        from_lat_raw = request.form.get('from_lat')
        from_lng_raw = request.form.get('from_lng')
        to_lat_raw = request.form.get('to_lat')
        to_lng_raw = request.form.get('to_lng')

        if from_lat_raw and from_lng_raw:
            f_lat, f_lng = float(from_lat_raw), float(from_lng_raw)
        else:
            f_lat, f_lng = get_city_coordinates(from_city)

        if to_lat_raw and to_lng_raw:
            t_lat, t_lng = float(to_lat_raw), float(to_lng_raw)
        else:
            t_lat, t_lng = get_city_coordinates(to_city)

        if not departure_time_str or not departure_time_str.strip():
            flash("Kérjük, válassz ki egy indulási dátumot és időpontot!", "danger")
            return render_template('create_ride.html', cars=user_cars)

        try:
            dep_datetime = datetime.strptime(departure_time_str, '%Y-%m-%dT%H:%M')
        except (ValueError, TypeError):
            try:
                dep_datetime = datetime.strptime(departure_time_str, '%Y-%m-%d %H:%M')
            except (ValueError, TypeError):
                flash("Érvénytelen dátum formátum!", "danger")
                return render_template('create_ride.html', cars=user_cars)

        if car_option == 'new' or not user_cars:
            new_car = Car(
                owner_id=current_user_id,
                brand=request.form.get('new_brand', 'Egyedi'),
                model=request.form.get('new_model', 'Model'),
                color=request.form.get('new_color', 'Fekete'),
                plate_num=request.form.get('new_plate_num', 'AB00XYZ'),
                seats=int(seats) if seats else 4
            )
            db.session.add(new_car)
            db.session.commit()
            car_id = new_car.car_id
        else:
            car_id = int(car_option)

        new_trip = Trip(
            driver_id=current_user_id, car_id=car_id,
            start_city=from_city, destination_city=to_city,
            start_latitude=f_lat, start_longitude=f_lng,
            destination_latitude=t_lat, destination_longitude=t_lng,
            departure_time=dep_datetime, estimated_arival_time=dep_datetime,
            price_per_seat=float(price) if price else 0.0, available_seats=int(seats) if seats else 1
        )
        db.session.add(new_trip)
        db.session.commit()

        return redirect(url_for('search'))

    return render_template('create_ride.html', cars=user_cars)

# --- BEJELENTKEZÉS ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        is_valid = False
        if user:
            is_valid = user.check_password(password)

        if user and is_valid:
            session['user_id'] = user.user_id
            session['user_name'] = user.full_name
            flash("Sikeres bejelentkezés!", "success")
            return redirect(url_for('home'))
        else:
            flash("Hibás e-mail cím vagy jelszó!", "danger")

    return render_template('login.html')

# --- REGISZTRÁCIÓ ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not full_name or not email or not password:
            flash("Minden kötelező mezőt ki kell tölteni!", "danger")
            return render_template('register.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Ezzel az e-mail címmel már létezik fiók!", "warning")
            return render_template('register.html')

        new_user = User(full_name=full_name, email=email, password_hash=password)

        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.user_id
        session['user_name'] = new_user.full_name
        flash("Sikeres regisztráció! Üdvözlünk a RIDEWMY-n!", "success")
        return redirect(url_for('home'))

    return render_template('register.html')

# --- KIJELENTKEZÉS ---
@app.route('/logout')
def logout():
    session.clear()
    flash("Sikeresen kijelentkeztél.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
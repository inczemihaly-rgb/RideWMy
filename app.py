import math
import unicodedata
import requests
from datetime import datetime, timedelta
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import func
from models import db, User, Car, Trip, Booking, Review

app = Flask(__name__)
app.secret_key = 'ridewmy_secret_key'

# XAMPP MySQL kapcsolódásasdasd
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@127.0.0.1/ridewmy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def init_seed_data():
    if User.query.count() == 0:
        print("-> Kezdő tesztadatok létrehozása (Sofőrök és Utasok)...")
        driver1 = User(full_name="Kovács Anna", email="anna@ridewmy.hu", password_hash="hash1")
        driver2 = User(full_name="Nagy Péter", email="peter@ridewmy.hu", password_hash="hash2")
        passenger = User(full_name="Szilárd T.", email="szilard@ridewmy.hu", password_hash="hash3")
        
        db.session.add_all([driver1, driver2, passenger])
        db.session.commit()

        car1 = Car(owner_id=driver1.user_id, brand="Toyota", model="Prius", color="Fehér", plate_num="ABC-123", seats=4)
        car2 = Car(owner_id=driver2.user_id, brand="Volkswagen", model="Passat", color="Ezüst", plate_num="XYZ-789", seats=4)
        db.session.add_all([car1, car2])
        db.session.commit()

        trip1 = Trip(
            driver_id=driver1.user_id, car_id=car1.car_id,
            start_latitude=46.5425, start_longitude=24.5575, # Marosvásárhely
            destination_latitude=46.7712, destination_longitude=23.6236, # Kolozsvár
            departure_time=datetime.now() + timedelta(days=1),
            estimated_arival_time=datetime.now() + timedelta(days=1, hours=2, minutes=15),
            price_per_seat=35.0, available_seats=3
        )
        trip2 = Trip(
            driver_id=driver2.user_id, car_id=car2.car_id,
            start_latitude=45.6579, start_longitude=25.6012, # Brassó
            destination_latitude=45.8636, destination_longitude=25.7878, # Sepsiszentgyörgy
            departure_time=datetime.now() + timedelta(days=2),
            estimated_arival_time=datetime.now() + timedelta(days=2, hours=1, minutes=15),
            price_per_seat=25.0, available_seats=2
        )
        db.session.add_all([trip1, trip2])
        db.session.commit()

with app.app_context():
    db.create_all()
    init_seed_data()

PRELOADED_COORDINATES = {
    "barot": (46.0747, 25.6025), "farkaslaka": (46.3811, 25.2153),
    "marosvasarhely": (46.5425, 24.5575), "kolozsvar": (46.7712, 23.6236),
    "brasso": (45.6579, 25.6012), "sepsiszentgyorgy": (45.8636, 25.7878),
    "szekelyudvarhely": (46.3053, 25.2936), "csikszereda": (46.3606, 25.8016)
}

GEO_CACHE = dict(PRELOADED_COORDINATES)
REVERSE_GEO_CACHE = {}

def remove_accents(input_str):
    if not input_str: return ""
    replacements = {'ț': 't', 'Ț': 't', 'ș': 's', 'Ș': 's', 'ă': 'a', 'Ă': 'a', 'î': 'i', 'Î': 'i', 'â': 'a', 'Â': 'a'}
    for text_char, clean_char in replacements.items():
        input_str = input_str.replace(text_char, clean_char)
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower().strip()

def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2): return float('inf')
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def format_duration(seconds):
    if not seconds or seconds <= 0: return "30 perc"
    minutes = int(seconds / 60)
    hours, rem_min = minutes // 60, minutes % 60
    return f"{hours} óra {rem_min} perc" if hours > 0 and rem_min > 0 else (f"{hours} óra" if hours > 0 else f"{rem_min} perc")

def get_osrm_duration_seconds(start_coords, dest_coords):
    try:
        lon1, lat1 = start_coords[1], start_coords[0]
        lon2, lat2 = dest_coords[1], dest_coords[0]
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
        response = requests.get(url, headers={'User-Agent': 'RideWMy-App/1.0'}, timeout=2.5)
        data = response.json()
        if data.get('code') == 'Ok' and len(data.get('routes', [])) > 0:
            return data['routes'][0]['duration']
    except Exception: pass
    return None

def calculate_estimated_arrival(start_coords, dest_coords, dep_datetime):
    if not start_coords or not dest_coords or not dep_datetime:
        return dep_datetime + timedelta(hours=1) if dep_datetime else datetime.now()
    duration_sec = get_osrm_duration_seconds(start_coords, dest_coords)
    travel_minutes = int(duration_sec / 60) if duration_sec else max(20, int((haversine_km(start_coords[0], start_coords[1], dest_coords[0], dest_coords[1]) / 60.0) * 60))
    return dep_datetime + timedelta(minutes=travel_minutes)

def get_coords_for_city(city_name):
    if not city_name: return None
    clean_key = remove_accents(city_name)
    if clean_key in GEO_CACHE:
        coords = GEO_CACHE[clean_key]
        REVERSE_GEO_CACHE[(round(coords[0], 3), round(coords[1], 3))] = city_name
        return coords
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={quote(city_name)}&countrycodes=ro&limit=1"
        res = requests.get(url, headers={'User-Agent': 'RideWMy-App/1.0'}, timeout=2.5).json()
        if res:
            coords = (float(res[0]['lat']), float(res[0]['lon']))
            GEO_CACHE[clean_key] = coords
            REVERSE_GEO_CACHE[(round(coords[0], 3), round(coords[1], 3))] = city_name
            return coords
    except Exception: pass
    return None

def get_city_name(lat, lng):
    if None in (lat, lng): return "Ismeretlen"
    lat_f, lng_f = round(float(lat), 3), round(float(lng), 3)
    if (lat_f, lng_f) in REVERSE_GEO_CACHE: return REVERSE_GEO_CACHE[(lat_f, lng_f)]
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat_f}&lon={lng_f}&zoom=14&addressdetails=1"
        res = requests.get(url, headers={'User-Agent': 'RideWMy-App/1.0'}, timeout=2.5).json()
        city = res.get('address', {}).get('city') or res.get('address', {}).get('town') or "Erdély"
        REVERSE_GEO_CACHE[(lat_f, lng_f)] = city
        return city
    except Exception: pass
    return "Erdély"

def get_driver_rating(driver_id):
    if not driver_id: return "5.0"
    avg_rating = db.session.query(func.avg(Review.rating))\
        .join(Booking, Review.booking_id == Booking.booking_id)\
        .join(Trip, Booking.trip_id == Trip.trip_id)\
        .filter(Trip.driver_id == driver_id)\
        .scalar()
    return f"{float(avg_rating):.1f}" if avg_rating is not None else "5.0"

# --- KEZDŐLAP (HOME) ---
@app.route('/')
def home():
    # Csak olyan utak jelennek meg a főoldalon, ahol van szabad hely (available_seats > 0)
    random_trips_db = Trip.query.filter(Trip.available_seats > 0).order_by(func.rand()).limit(3).all()
    popular_rides = []

    for trip in random_trips_db:
        from_city = get_city_name(trip.start_latitude, trip.start_longitude)
        to_city = get_city_name(trip.destination_latitude, trip.destination_longitude)
        start_hour = trip.departure_time.strftime('%H:%M') if trip.departure_time else "08:00"
        end_time = trip.estimated_arival_time.strftime('%H:%M') if trip.estimated_arival_time else "10:15"
        calculated_rating = get_driver_rating(trip.driver_id)

        popular_rides.append({
            "id": trip.trip_id,
            "driver": trip.driver.full_name if trip.driver else "Ismeretlen",
            "rating": calculated_rating,
            "from": from_city,
            "to": to_city,
            "price": f"{int(trip.price_per_seat)} RON",
            "seats": f"{trip.available_seats} szabad hely",
            "startHour": start_hour,
            "endTime": end_time
        })

    return render_template('home.html', rides=popular_rides)

# --- UTAK KERESÉSE (SEARCH / INDEX) ---
@app.route('/search')
def search():
    search_from = request.args.get('from', '').strip()
    search_to = request.args.get('to', '').strip()
    search_date = request.args.get('date', '').strip()
    search_seats = request.args.get('seats', '').strip()

    # Csak olyan utakat kérünk le az adatbázisból a keresőben, ahol available_seats > 0
    trips_from_db = Trip.query.filter(Trip.available_seats > 0).all()
    rides_data = []

    from_search_coords = get_coords_for_city(search_from) if search_from else None
    to_search_coords = get_coords_for_city(search_to) if search_to else None
    norm_search_from = remove_accents(search_from)
    norm_search_to = remove_accents(search_to)

    for trip in trips_from_db:
        from_city = get_city_name(trip.start_latitude, trip.start_longitude)
        to_city = get_city_name(trip.destination_latitude, trip.destination_longitude)

        match_from = True
        if search_from:
            match_from = False
            if from_search_coords and trip.start_latitude and trip.start_longitude:
                dist_from = haversine_km(float(trip.start_latitude), float(trip.start_longitude), from_search_coords[0], from_search_coords[1])
                if dist_from <= 25.0: match_from = True
            if not match_from:
                norm_from = remove_accents(from_city)
                match_from = norm_search_from in norm_from or norm_from in norm_search_from

        match_to = True
        if search_to:
            match_to = False
            if to_search_coords and trip.destination_latitude and trip.destination_longitude:
                dist_to = haversine_km(float(trip.destination_latitude), float(trip.destination_longitude), to_search_coords[0], to_search_coords[1])
                if dist_to <= 25.0: match_to = True
            if not match_to:
                norm_to = remove_accents(to_city)
                match_to = norm_search_to in norm_to or norm_to in norm_search_to

        match_date = True
        if search_date and trip.departure_time:
            match_date = (trip.departure_time.strftime('%Y-%m-%d') == search_date)

        match_seats = True
        if search_seats:
            try:
                match_seats = (trip.available_seats >= int(search_seats))
            except ValueError: pass

        if match_from and match_to and match_date and match_seats:
            formatted_date = trip.departure_time.strftime('%Y. %m. %d. %H:%M') if trip.departure_time else "2026. 11. 02. 10:00"
            start_hour = trip.departure_time.strftime('%H:%M') if trip.departure_time else "10:00"
            end_time = trip.estimated_arival_time.strftime('%H:%M') if trip.estimated_arival_time else "12:00"

            duration_str = ""
            if trip.departure_time and trip.estimated_arival_time:
                diff_sec = (trip.estimated_arival_time - trip.departure_time).total_seconds()
                duration_str = format_duration(diff_sec)
            
            dist_str = ""
            if trip.start_latitude and trip.destination_latitude:
                d_km = haversine_km(float(trip.start_latitude), float(trip.start_longitude), float(trip.destination_latitude), float(trip.destination_longitude))
                dist_str = f"{int(d_km)} km"

            calculated_rating = get_driver_rating(trip.driver_id)

            rides_data.append({
                "id": trip.trip_id,
                "driver": trip.driver.full_name if trip.driver else "Ismeretlen",
                "car": f"{trip.car.brand} {trip.car.model}" if trip.car else "",
                "rating": calculated_rating,
                "from": from_city, "to": to_city,
                "fromLat": float(trip.start_latitude) if trip.start_latitude else None,
                "fromLng": float(trip.start_longitude) if trip.start_longitude else None,
                "toLat": float(trip.destination_latitude) if trip.destination_latitude else None,
                "toLng": float(trip.destination_longitude) if trip.destination_longitude else None,
                "price": f"{int(trip.price_per_seat)} RON",
                "seats": f"{trip.available_seats} szabad hely",
                "startTime": formatted_date,
                "startHour": start_hour,
                "endTime": end_time,
                "duration": duration_str,
                "distance": dist_str
            })

    return render_template('index.html', rides=rides_data)

# --- UTAZÁS RÉSZLETI (RIDE DETAILS) ---
@app.route('/ride/<int:trip_id>')
def ride_details(trip_id):
    trip = db.session.get(Trip, trip_id)
    if not trip:
        return redirect(url_for('search'))

    from_city = get_city_name(trip.start_latitude, trip.start_longitude)
    to_city = get_city_name(trip.destination_latitude, trip.destination_longitude)
    
    formatted_date = trip.departure_time.strftime('%Y. %B %d.').lower() if trip.departure_time else "2026. október 25."
    start_hour = trip.departure_time.strftime('%H:%M') if trip.departure_time else "08:00"
    end_hour = trip.estimated_arival_time.strftime('%H:%M') if trip.estimated_arival_time else "10:15"

    duration_str = "2 óra 15 perc"
    if trip.departure_time and trip.estimated_arival_time:
        diff_sec = (trip.estimated_arival_time - trip.departure_time).total_seconds()
        duration_str = format_duration(diff_sec)

    calculated_rating = get_driver_rating(trip.driver_id)
    car_name = f"{trip.car.brand} {trip.car.model} - {trip.car.color}" if trip.car else "Volkswagen Passat - Ezüst"

    ride_detail = {
        "id": trip.trip_id,
        "driver_name": trip.driver.full_name if trip.driver else "Szilárd T.",
        "rating": calculated_rating,
        "date_formatted": formatted_date,
        "from": from_city,
        "to": to_city,
        "from_lat": float(trip.start_latitude) if trip.start_latitude else 46.5425,
        "from_lng": float(trip.start_longitude) if trip.start_longitude else 24.5575,
        "to_lat": float(trip.destination_latitude) if trip.destination_latitude else 46.7712,
        "to_lng": float(trip.destination_longitude) if trip.destination_longitude else 23.6236,
        "start_hour": start_hour,
        "end_hour": end_hour,
        "duration": duration_str,
        "car": car_name,
        "price_num": int(trip.price_per_seat),
        "available_seats": trip.available_seats
    }

    return render_template('ride_details.html', ride=ride_detail)

# --- FOGLALÁS VÉGREHAJTÁSA ---
@app.route('/book-ride', methods=['POST'])
def book_ride():
    trip_id = int(request.form.get('trip_id'))
    seats_requested = int(request.form.get('seats', 1))
    
    passenger = User.query.filter(User.full_name.like('%Szilárd%')).first()
    passenger_id = passenger.user_id if passenger else 3

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

@app.route('/create-ride', methods=['GET', 'POST'])
def create_ride():
    current_user_id = 1
    if request.method == 'POST':
        from_city = request.form.get('from')
        to_city = request.form.get('to')
        departure_time_str = request.form.get('datetime')
        seats = request.form.get('seats')
        price = request.form.get('price')
        car_option = request.form.get('car_id')

        # Dátum meglétének szigorú ellenőrzése
        if not departure_time_str or not departure_time_str.strip():
            flash("Kérjük, válassz ki egy indulási dátumot és időpontot!", "danger")
            user_cars = Car.query.filter_by(owner_id=current_user_id).all() or Car.query.all()
            return render_template('create_ride.html', cars=user_cars)

        try:
            dep_datetime = datetime.strptime(departure_time_str, '%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            flash("Érvénytelen dátum formátum!", "danger")
            user_cars = Car.query.filter_by(owner_id=current_user_id).all() or Car.query.all()
            return render_template('create_ride.html', cars=user_cars)

        if car_option == 'new':
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
            car_id = int(car_option) if car_option else 1

        start_coords = get_coords_for_city(from_city) or (46.5425, 24.5575)
        dest_coords = get_coords_for_city(to_city) or (46.5425, 24.5575)

        estimated_arrival = calculate_estimated_arrival(start_coords, dest_coords, dep_datetime)

        new_trip = Trip(
            driver_id=current_user_id, car_id=car_id,
            start_latitude=start_coords[0], start_longitude=start_coords[1],
            destination_latitude=dest_coords[0], destination_longitude=dest_coords[1],
            departure_time=dep_datetime, estimated_arival_time=estimated_arrival,
            price_per_seat=float(price) if price else 0.0, available_seats=int(seats) if seats else 1
        )
        db.session.add(new_trip)
        db.session.commit()

        return redirect(url_for('search'))

    user_cars = Car.query.filter_by(owner_id=current_user_id).all() or Car.query.all()
    return render_template('create_ride.html', cars=user_cars)


if __name__ == '__main__':
    app.run(debug=True)
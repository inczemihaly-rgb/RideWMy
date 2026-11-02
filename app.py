import math
import unicodedata
import requests
from datetime import datetime, timedelta
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import func
from models import db, User, Car, Trip, Booking, Review

app = Flask(__name__)

# XAMPP MySQL kapcsolódás
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ridewmy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

PRELOADED_COORDINATES = {
    "barot": (46.0747, 25.6025),
    "farkaslaka": (46.3811, 25.2153),
    "hatszeg": (45.6072, 22.9497),
    "horezu": (45.1481, 24.0131),
    "marosvasarhely": (46.5425, 24.5575),
    "kolozsvar": (46.7712, 23.6236),
    "brasso": (45.6579, 25.6012),
    "nagyszeben": (45.7983, 24.1256),
    "sepsiszentgyorgy": (45.8636, 25.7878),
    "szekelyudvarhely": (46.3053, 25.2936),
    "csikszereda": (46.3606, 25.8016),
    "gyergyoszentmiklos": (46.7225, 25.6006),
    "kezdivasarhely": (45.8486, 26.1367),
    "szekelykeresztur": (46.2917, 25.0356),
    "korond": (46.4686, 25.1764),
    "parajd": (46.5558, 25.1274),
    "szovata": (46.5986, 25.0742),
    "nagyvarad": (47.0515, 21.9402),
    "arad": (46.1866, 21.3123),
    "temesvar": (45.7537, 21.2257),
    "bukarest": (44.4323, 26.1063)
}

GEO_CACHE = dict(PRELOADED_COORDINATES)
REVERSE_GEO_CACHE = {}

def remove_accents(input_str):
    if not input_str:
        return ""
    replacements = {'ț': 't', 'Ț': 't', 'ș': 's', 'Ș': 's', 'ă': 'a', 'Ă': 'a', 'î': 'i', 'Î': 'i', 'â': 'a', 'Â': 'a'}
    for text_char, clean_char in replacements.items():
        input_str = input_str.replace(text_char, clean_char)
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower().strip()

def haversine_km(lat1, lon1, lat2, lon2):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def format_duration(seconds):
    if not seconds or seconds <= 0:
        return "30 perc"
    minutes = int(seconds / 60)
    hours = minutes // 60
    rem_min = minutes % 60
    if hours > 0:
        return f"{hours} óra {rem_min} perc" if rem_min > 0 else f"{hours} óra"
    return f"{rem_min} perc"

def get_osrm_duration_seconds(start_coords, dest_coords):
    try:
        lon1, lat1 = start_coords[1], start_coords[0]
        lon2, lat2 = dest_coords[1], dest_coords[0]
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
        headers = {'User-Agent': 'RideWMy-App/1.0'}
        response = requests.get(url, headers=headers, timeout=2.5)
        data = response.json()
        if data.get('code') == 'Ok' and len(data.get('routes', [])) > 0:
            return data['routes'][0]['duration']
    except Exception as e:
        print("OSRM API Hiba:", e)
    return None

def calculate_estimated_arrival(start_coords, dest_coords, dep_datetime):
    if not start_coords or not dest_coords or not dep_datetime:
        return dep_datetime + timedelta(hours=1) if dep_datetime else datetime.now()
    
    duration_sec = get_osrm_duration_seconds(start_coords, dest_coords)
    if duration_sec:
        travel_minutes = int(duration_sec / 60)
    else:
        dist_km = haversine_km(start_coords[0], start_coords[1], dest_coords[0], dest_coords[1])
        travel_minutes = max(20, int((dist_km / 60.0) * 60))
    
    return dep_datetime + timedelta(minutes=travel_minutes)

def get_coords_for_city(city_name):
    if not city_name:
        return None
    clean_key = remove_accents(city_name)
    if clean_key in GEO_CACHE:
        coords = GEO_CACHE[clean_key]
        REVERSE_GEO_CACHE[(round(coords[0], 3), round(coords[1], 3))] = city_name
        return coords

    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={quote(city_name)}&countrycodes=ro&accept-language=hu,ro&limit=1"
        headers = {'User-Agent': 'RideWMy-App/1.0'}
        response = requests.get(url, headers=headers, timeout=2.5)
        data = response.json()
        if data:
            coords = (float(data[0]['lat']), float(data[0]['lon']))
            GEO_CACHE[clean_key] = coords
            REVERSE_GEO_CACHE[(round(coords[0], 3), round(coords[1], 3))] = city_name
            return coords
    except Exception:
        pass
    return None

def get_city_name(lat, lng):
    if lat is None or lng is None:
        return "Ismeretlen"
    lat_f, lng_f = round(float(lat), 3), round(float(lng), 3)
    if (lat_f, lng_f) in REVERSE_GEO_CACHE:
        return REVERSE_GEO_CACHE[(lat_f, lng_f)]

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat_f}&lon={lng_f}&zoom=14&addressdetails=1&accept-language=hu,ro"
        headers = {'User-Agent': 'RideWMy-App/1.0'}
        response = requests.get(url, headers=headers, timeout=2.5)
        data = response.json()
        address = data.get('address', {})
        city_name = address.get('city') or address.get('town') or address.get('municipality') or address.get('village') or "Erdélyi település"
        REVERSE_GEO_CACHE[(lat_f, lng_f)] = city_name
        return city_name
    except Exception:
        pass
    return "Erdély"

# --- SOFŐR ÁTLAGOS ÉRTÉKELÉSÉNEK DINAMIKUS KISZÁMÍTÁSA ---
def get_driver_rating(driver_id):
    if not driver_id:
        return "5.0"
    
    avg_rating = db.session.query(func.avg(Review.rating))\
        .join(Booking, Review.booking_id == Booking.booking_id)\
        .join(Trip, Booking.trip_id == Trip.trip_id)\
        .filter(Trip.driver_id == driver_id)\
        .scalar()
    
    if avg_rating is not None:
        return f"{float(avg_rating):.1f}"
    return "5.0"  # Alapértelmezett kezdő érték, ha még nincs értékelés

@app.route('/')
def index():
    search_from = request.args.get('from', '').strip()
    search_to = request.args.get('to', '').strip()
    search_date = request.args.get('date', '').strip()
    search_seats = request.args.get('seats', '').strip()

    trips_from_db = Trip.query.all()
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
                if dist_from <= 25.0:
                    match_from = True
            if not match_from:
                norm_from = remove_accents(from_city)
                match_from = norm_search_from in norm_from or norm_from in norm_search_from

        match_to = True
        if search_to:
            match_to = False
            if to_search_coords and trip.destination_latitude and trip.destination_longitude:
                dist_to = haversine_km(float(trip.destination_latitude), float(trip.destination_longitude), to_search_coords[0], to_search_coords[1])
                if dist_to <= 25.0:
                    match_to = True
            if not match_to:
                norm_to = remove_accents(to_city)
                match_to = norm_search_to in norm_to or norm_to in norm_search_to

        match_date = True
        if search_date and trip.departure_time:
            match_date = (trip.departure_time.strftime('%Y-%m-%d') == search_date)

        match_seats = True
        if search_seats:
            try:
                needed_seats = int(search_seats)
                match_seats = (trip.available_seats >= needed_seats)
            except ValueError:
                pass

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

            car_info = f"{trip.car.brand} {trip.car.model}" if trip.car else ""

            # Sofőr dinamikus értékelésének lekérése az adatbázisból
            calculated_rating = get_driver_rating(trip.driver_id)

            rides_data.append({
                "id": trip.trip_id,
                "driver": trip.driver.full_name if trip.driver else "Ismeretlen",
                "car": car_info,
                "rating": calculated_rating,
                "from": from_city,
                "to": to_city,
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

        if car_option == 'new':
            new_brand = request.form.get('new_brand', 'Egyedi')
            new_model = request.form.get('new_model', 'Model')
            new_color = request.form.get('new_color', 'Fekete')
            new_plate = request.form.get('new_plate_num', 'AB00XYZ')

            new_car = Car(
                owner_id=current_user_id,
                brand=new_brand,
                model=new_model,
                color=new_color,
                plate_num=new_plate,
                seats=int(seats) if seats else 4
            )
            db.session.add(new_car)
            db.session.commit()
            car_id = new_car.car_id
        else:
            car_id = int(car_option) if car_option else 1

        start_coords = get_coords_for_city(from_city) or (46.5425, 24.5575)
        dest_coords = get_coords_for_city(to_city) or (46.5425, 24.5575)

        try:
            dep_datetime = datetime.strptime(departure_time_str, '%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            dep_datetime = datetime.now()

        estimated_arrival = calculate_estimated_arrival(start_coords, dest_coords, dep_datetime)

        new_trip = Trip(
            driver_id=current_user_id,
            car_id=car_id,
            start_latitude=start_coords[0],
            start_longitude=start_coords[1],
            destination_latitude=dest_coords[0],
            destination_longitude=dest_coords[1],
            departure_time=dep_datetime,
            estimated_arival_time=estimated_arrival,
            price_per_seat=float(price) if price else 0.0,
            available_seats=int(seats) if seats else 1
        )

        db.session.add(new_trip)
        db.session.commit()

        return redirect(url_for('index'))

    user_cars = Car.query.filter_by(owner_id=current_user_id).all()
    if not user_cars:
        user_cars = Car.query.all()

    return render_template('create_ride.html', cars=user_cars)

@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    current_user_id = 1

    if request.method == 'POST':
        rating_val = request.form.get('rating', 5)
        comment_val = request.form.get('comment', '')
        booking_id_val = request.form.get('booking_id', 1)

        user = User.query.get(current_user_id)
        if not user:
            user = User(user_id=current_user_id, full_name="Szilárd T.", email="szilard@test.com")
            db.session.add(user)
            db.session.commit()

        booking = Booking.query.get(int(booking_id_val))
        if not booking:
            trip = Trip.query.first()
            if not trip:
                car = Car.query.first()
                if not car:
                    car = Car(owner_id=current_user_id, brand="VW", model="Golf", seats=4)
                    db.session.add(car)
                    db.session.commit()
                trip = Trip(driver_id=current_user_id, car_id=car.car_id, available_seats=4)
                db.session.add(trip)
                db.session.commit()

            booking = Booking(
                booking_id=int(booking_id_val),
                trip_id=trip.trip_id,
                pasinger_id=current_user_id,
                seats_bookd=1
            )
            db.session.add(booking)
            db.session.commit()

        new_review = Review(
            booking_id=booking.booking_id,
            reviewer_id=current_user_id,
            rating=int(rating_val),
            comment=comment_val
        )
        db.session.add(new_review)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('reviews.html')

if __name__ == '__main__':
    app.run(debug=True)
<<<<<<< HEAD
from flask import Flask, render_template, request, redirect, url_for, session
=======
import math
import random
from datetime import datetime, timedelta
import json
import urllib.parse
import urllib.request
from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy.exc import IntegrityError
>>>>>>> main
from models import db, User, Car, Trip, Booking, Review

app = Flask(__name__)
app.secret_key = 'ridewmy_super_secret_key'

# XAMPP MySQL kapcsolódás
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ridewmy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

<<<<<<< HEAD
# Ez a titkos kulcs kell a session (munkamenet) biztonságos működéséhez!
app.secret_key = 'ridewmy_super_secret_key_123'

# SQLAlchemy inicializálása
=======
>>>>>>> main
db.init_app(app)

with app.app_context():
    db.create_all()

DAYS_HU = ["hétfő", "kedd", "szerda", "csütörtök", "péntek", "szombat", "vasárnap"]
MONTHS_HU = ["", "január", "február", "március", "április", "május", "június",
             "július", "augusztus", "szeptember", "október", "november", "december"]

@app.context_processor
def inject_pending_notifications():
    pending_count = 0
    user_id = session.get('user_id')
    if user_id:
        try:
            driver_trip_ids = [t.trip_id for t in Trip.query.filter_by(driver_id=user_id).all()]
            if driver_trip_ids:
                pending_count = Booking.query.filter(
                    Booking.trip_id.in_(driver_trip_ids),
                    Booking.booking_status == False
                ).count()
        except Exception:
            pending_count = 0
    return dict(pending_requests_count=pending_count)

def format_date_hu(dt):
    if not dt:
        return "2026. október 30., péntek"
    return f"{dt.year}. {MONTHS_HU[dt.month]} {dt.day}., {DAYS_HU[dt.weekday()]}"

def format_duration_hu(minutes):
    minutes = max(1, int(round(minutes)))
    hrs = minutes // 60
    mins = minutes % 60
    if hrs > 0:
        return f"{hrs} óra {mins} perc" if mins > 0 else f"{hrs} óra"
    return f"{mins} perc"

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

ROUTE_CACHE = {}

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_route_info(f_lat, f_lng, t_lat, t_lng):
    key = (round(float(f_lat), 4), round(float(f_lng), 4), round(float(t_lat), 4), round(float(t_lng), 4))
    if key in ROUTE_CACHE:
        return ROUTE_CACHE[key]
    try:
        url = f"https://router.project-osrm.org/route/v1/driving/{key[1]},{key[0]};{key[3]},{key[2]}?overview=false"
        req = urllib.request.Request(url, headers={'User-Agent': 'RideWmyApp/1.0'})
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode())
            if data.get('routes'):
                route = data['routes'][0]
                dur_mins = max(1, int(round(route['duration'] / 60)))
                dist_km = max(1, int(round(route['distance'] / 1000)))
                ROUTE_CACHE[key] = (dur_mins, dist_km)
                return dur_mins, dist_km
    except Exception:
        pass

    straight_km = haversine_km(key[0], key[1], key[2], key[3])
    dist_km = max(1, int(round(straight_km * 1.25)))
    dur_mins = max(5, int(round((dist_km / 65.0) * 60)))
    ROUTE_CACHE[key] = (dur_mins, dist_km)
    return dur_mins, dist_km

def get_trip_timing(trip):
    f_lat = float(trip.start_latitude) if trip.start_latitude else 46.5425
    f_lng = float(trip.start_longitude) if trip.start_longitude else 24.5575
    t_lat = float(trip.destination_latitude) if trip.destination_latitude else 46.7712
    t_lng = float(trip.destination_longitude) if trip.destination_longitude else 23.6236

    calc_mins, dist_km = calculate_route_info(f_lat, f_lng, t_lat, t_lng)

    if trip.departure_time and trip.estimated_arival_time and trip.estimated_arival_time > trip.departure_time:
        dur_mins = int((trip.estimated_arival_time - trip.departure_time).total_seconds() // 60)
        arrival_dt = trip.estimated_arival_time
    elif trip.departure_time:
        dur_mins = calc_mins
        arrival_dt = trip.departure_time + timedelta(minutes=dur_mins)
    else:
        dur_mins = calc_mins
        arrival_dt = None

    start_hour = trip.departure_time.strftime('%H:%M') if trip.departure_time else "08:00"
    end_hour = arrival_dt.strftime('%H:%M') if arrival_dt else "10:15"
    return start_hour, end_hour, format_duration_hu(dur_mins), f"{dist_km} km"

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
        start_hour, end_hour, duration_str, distance_str = get_trip_timing(trip)
        rides_data.append({
            "id": trip.trip_id,
            "driver_id": trip.driver_id,
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
            "startHour": start_hour,
            "endTime": end_hour,
            "duration": duration_str,
            "distance": distance_str,
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

# --- PROFIL OLDAL ---
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("A profil megtekintéséhez kérjük, jelentkezz be!", "warning")
        return redirect(url_for('login'))

    current_user_id = session['user_id']
    user = db.session.get(User, current_user_id)
    if not user:
        session.clear()
        return redirect(url_for('login'))

    user_cars = Car.query.filter_by(owner_id=current_user_id).all()
    primary_car = user_cars[0] if user_cars else None

    avg_rating = "5.0"
    review_count = 0
    driver_trips = Trip.query.filter_by(driver_id=current_user_id).all()
    try:
        driver_trip_ids = [t.trip_id for t in driver_trips]
        if driver_trip_ids:
            bookings_for_driver = Booking.query.filter(Booking.trip_id.in_(driver_trip_ids)).all()
            booking_ids = [b.booking_id for b in bookings_for_driver]
            if booking_ids:
                user_reviews = Review.query.filter(Review.booking_id.in_(booking_ids)).all()
                review_count = len(user_reviews)
                if review_count > 0:
                    avg_val = sum(r.rating for r in user_reviews) / review_count
                    avg_rating = f"{avg_val:.1f}"
    except Exception:
        pass

    now = datetime.now()
    user_bookings = Booking.query.filter_by(pasinger_id=current_user_id).all()
    upcoming_bookings = []
    past_bookings = []

    for b in user_bookings:
        if not b.trip:
            continue
        t = b.trip
        start_hour, end_hour, _, _ = get_trip_timing(t)
        item = {
            "booking_id": b.booking_id,
            "trip_id": t.trip_id,
            "is_confirmed": bool(b.booking_status),
            "date_str": format_date_hu(t.departure_time),
            "start_hour": start_hour,
            "end_hour": end_hour,
            "from_city": t.start_city or "Kiindulás",
            "to_city": t.destination_city or "Úticél",
            "seats_booked": b.seats_bookd,
            "total_price": int(t.price_per_seat * b.seats_bookd)
        }
        if t.departure_time and t.departure_time < now:
            past_bookings.append(item)
        else:
            upcoming_bookings.append(item)

    my_trips = []
    pending_bookings = []

    for t in driver_trips:
        start_hour, end_hour, _, _ = get_trip_timing(t)
        trip_bookings = Booking.query.filter_by(trip_id=t.trip_id).all()
        pending_count = 0
        confirmed_count = 0

        for tb in trip_bookings:
            if not tb.booking_status:
                pending_count += 1
                passenger_user = db.session.get(User, tb.pasinger_id)
                pending_bookings.append({
                    "booking_id": tb.booking_id,
                    "trip_id": t.trip_id,
                    "passenger_name": passenger_user.full_name if passenger_user else "Utas",
                    "from_city": t.start_city or "Kiindulás",
                    "to_city": t.destination_city or "Úticél",
                    "date_str": format_date_hu(t.departure_time),
                    "start_hour": start_hour,
                    "seats": tb.seats_bookd,
                    "total_price": int((t.price_per_seat or 0) * tb.seats_bookd)
                })
            else:
                confirmed_count += 1

        my_trips.append({
            "trip_id": t.trip_id,
            "date_str": format_date_hu(t.departure_time),
            "start_hour": start_hour,
            "end_hour": end_hour,
            "from_city": t.start_city or "Kiindulás",
            "to_city": t.destination_city or "Úticél",
            "available_seats": t.available_seats,
            "price_per_seat": int(t.price_per_seat) if t.price_per_seat else 0,
            "car_name": f"{t.car.brand} {t.car.model}" if t.car else "Nincs megadva",
            "pending_count": pending_count,
            "confirmed_count": confirmed_count
        })

    # Elöl legyenek azok a meghirdetett utak, amelyekre már jelentkeztek
    my_trips.sort(key=lambda x: (-x["pending_count"], -x["confirmed_count"]))

    phone_display = user.phone if user.phone else "Nincs megadva"

    return render_template(
        'profile.html',
        user=user,
        primary_car=primary_car,
        avg_rating=avg_rating,
        review_count=review_count,
        phone_display=phone_display,
        upcoming_bookings=upcoming_bookings,
        past_bookings=past_bookings,
        my_trips=my_trips,
        pending_bookings=pending_bookings
    )

@app.route('/profile/edit', methods=['POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    current_user_id = session['user_id']
    user = db.session.get(User, current_user_id)
    if not user:
        session.clear()
        return redirect(url_for('login'))

    new_name = request.form.get('full_name', '').strip()
    new_phone = request.form.get('phone', '').strip()

    car_brand = request.form.get('car_brand', '').strip()
    car_model = request.form.get('car_model', '').strip()
    car_color = request.form.get('car_color', '').strip()
    car_plate = request.form.get('car_plate', '').strip().replace(" ", "").replace("-", "").upper()

    if car_plate and len(car_plate) > 7:
        flash("A rendszám maximum 7 karakter hosszú lehet (pl. MS05KAK)!", "danger")
        return redirect(url_for('profile'))

    if new_name:
        user.full_name = new_name
        session['user_name'] = new_name
    user.phone = new_phone if new_phone else None

    user_cars = Car.query.filter_by(owner_id=current_user_id).all()
    primary_car = user_cars[0] if user_cars else None

    if primary_car:
        if car_brand:
            primary_car.brand = car_brand
        if car_model:
            primary_car.model = car_model
        if car_color:
            primary_car.color = car_color
        if car_plate:
            primary_car.plate_num = car_plate
    elif any([car_brand, car_model, car_color, car_plate]):
        if not (car_brand and car_model and car_plate):
            flash("Új autó rögzítéséhez a márka, modell és rendszám megadása kötelező!", "warning")
            return redirect(url_for('profile'))
        new_car = Car(
            owner_id=current_user_id,
            brand=car_brand,
            model=car_model,
            color=car_color or "Ismeretlen",
            plate_num=car_plate,
            seats=4
        )
        db.session.add(new_car)

    try:
        db.session.commit()
        flash("Saját profil adatok sikeresen frissítve!", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Hiba: Ez a rendszám már foglalt!", "danger")

    return redirect(url_for('profile'))

@app.route('/profile/delete', methods=['POST'])
def delete_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])
    if user:
        for b in user.bookings:
            if b.trip:
                b.trip.available_seats += b.seats_bookd
        db.session.delete(user)
        db.session.commit()

    session.clear()
    flash("A profilod és minden hozzá tartozó adat véglegesen törölve lett.", "info")
    return redirect(url_for('home'))

# --- UTAZÁS KEZELÉSE (KÜLÖN OLDALON) ---
@app.route('/manage-ride/<int:trip_id>', methods=['GET', 'POST'])
def manage_ride(trip_id):
    if 'user_id' not in session:
        flash("Az utazás kezeléséhez kérjük, jelentkezz be!", "warning")
        return redirect(url_for('login'))

    current_user_id = session['user_id']
    user = db.session.get(User, current_user_id)
    if not user:
        session.clear()
        return redirect(url_for('login'))

    trip = db.session.get(Trip, trip_id)
    if not trip or trip.driver_id != current_user_id:
        flash("Nincs jogosultságod ennek az utazásnak a kezeléséhez.", "danger")
        return redirect(url_for('profile'))

    if request.method == 'POST':
        new_from = request.form.get('start_city', '').strip()
        new_to = request.form.get('destination_city', '').strip()
        dt_str = request.form.get('datetime', '').strip()
        seats_str = request.form.get('available_seats', '').strip()
        price_str = request.form.get('price_per_seat', '').strip()

        from_lat_raw = request.form.get('from_lat', '').strip()
        from_lng_raw = request.form.get('from_lng', '').strip()
        to_lat_raw = request.form.get('to_lat', '').strip()
        to_lng_raw = request.form.get('to_lng', '').strip()

        if new_from:
            if from_lat_raw and from_lng_raw:
                trip.start_latitude = float(from_lat_raw)
                trip.start_longitude = float(from_lng_raw)
            elif new_from != trip.start_city:
                trip.start_latitude, trip.start_longitude = get_city_coordinates(new_from)
            trip.start_city = new_from

        if new_to:
            if to_lat_raw and to_lng_raw:
                trip.destination_latitude = float(to_lat_raw)
                trip.destination_longitude = float(to_lng_raw)
            elif new_to != trip.destination_city:
                trip.destination_latitude, trip.destination_longitude = get_city_coordinates(new_to)
            trip.destination_city = new_to

        if dt_str:
            try:
                dep_dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
                trip.departure_time = dep_dt
            except ValueError:
                pass

        if trip.departure_time:
            f_lat = float(trip.start_latitude) if trip.start_latitude else 46.5425
            f_lng = float(trip.start_longitude) if trip.start_longitude else 24.5575
            t_lat = float(trip.destination_latitude) if trip.destination_latitude else 46.7712
            t_lng = float(trip.destination_longitude) if trip.destination_longitude else 23.6236
            dur_mins, _ = calculate_route_info(f_lat, f_lng, t_lat, t_lng)
            trip.estimated_arival_time = trip.departure_time + timedelta(minutes=dur_mins)

        if seats_str.isdigit():
            trip.available_seats = max(0, int(seats_str))

        try:
            if price_str:
                trip.price_per_seat = max(1.0, float(price_str))
        except ValueError:
            pass

        db.session.commit()
        flash("A módosítások sikeresen elmentve!", "success")
        return redirect(url_for('manage_ride', trip_id=trip.trip_id))

    bookings = Booking.query.filter_by(trip_id=trip.trip_id).all()
    passengers = []
    booked_seats_total = 0

    for b in bookings:
        passenger_user = db.session.get(User, b.pasinger_id)
        if not passenger_user:
            continue
        booked_seats_total += b.seats_bookd
        passengers.append({
            "booking_id": b.booking_id,
            "full_name": passenger_user.full_name,
            "phone": passenger_user.phone if passenger_user.phone else "Nincs megadva telefonszám",
            "seats": b.seats_bookd,
            "is_confirmed": bool(b.booking_status)
        })

    total_seats = trip.available_seats + booked_seats_total
    datetime_value = trip.departure_time.strftime('%Y-%m-%d %H:%M') if trip.departure_time else ""

    return render_template(
        'manage_ride.html',
        user=user,
        trip=trip,
        passengers=passengers,
        booked_seats_total=booked_seats_total,
        total_seats=total_seats,
        datetime_value=datetime_value
    )

@app.route('/booking/<int:booking_id>/accept', methods=['POST'])
def accept_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    booking = db.session.get(Booking, booking_id)
    if booking and booking.trip and booking.trip.driver_id == session['user_id']:
        booking.booking_status = True
        db.session.commit()
        flash("Az utas jelentkezését elfogadtad!", "success")
        if request.form.get('redirect_to') == 'profile':
            return redirect(url_for('profile'))
        return redirect(url_for('manage_ride', trip_id=booking.trip_id))

    return redirect(url_for('profile'))

@app.route('/booking/<int:booking_id>/reject', methods=['POST'])
def reject_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    booking = db.session.get(Booking, booking_id)
    if booking and booking.trip and booking.trip.driver_id == session['user_id']:
        trip_id = booking.trip_id
        booking.trip.available_seats += booking.seats_bookd
        db.session.delete(booking)
        db.session.commit()
        flash("Az utas jelentkezését elutasítottad, a hely újra elérhető.", "info")
        if request.form.get('redirect_to') == 'profile':
            return redirect(url_for('profile'))
        return redirect(url_for('manage_ride', trip_id=trip_id))

    return redirect(url_for('profile'))

@app.route('/cancel-booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    booking = db.session.get(Booking, booking_id)
    if booking and booking.pasinger_id == session['user_id']:
        if booking.trip:
            booking.trip.available_seats += booking.seats_bookd
        db.session.delete(booking)
        db.session.commit()
        flash("A foglalás sikeresen lemondva.", "info")

    return redirect(url_for('profile'))

@app.route('/delete-trip/<int:trip_id>', methods=['POST'])
def delete_trip(trip_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    trip = db.session.get(Trip, trip_id)
    if trip and trip.driver_id == session['user_id']:
        db.session.delete(trip)
        db.session.commit()
        flash("A meghirdetett utad törölve lett.", "info")

    return redirect(url_for('profile'))

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
    start_hour, end_hour, duration_str, distance_str = get_trip_timing(trip)

    car_name = f"{trip.car.brand} {trip.car.model} - {trip.car.color}" if trip.car else "Volkswagen Passat - Ezüst"
    driver_name = trip.driver.full_name if hasattr(trip.driver, 'full_name') else getattr(trip.driver, 'name', 'Sofőr')

    ride_detail = {
        "id": trip.trip_id,
        "driver_id": trip.driver_id,
        "is_own_ride": (session.get('user_id') == trip.driver_id),
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
        "duration": duration_str,
        "distance": distance_str,
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
    if not trip:
        return redirect(url_for('search'))

    if trip.driver_id == passenger_id:
        flash("A saját meghirdetett utadat nem foglalhatod le!", "warning")
        return redirect(url_for('manage_ride', trip_id=trip_id))

    if trip.available_seats >= seats_requested:
        trip.available_seats -= seats_requested
        booking = Booking(
            trip_id=trip.trip_id,
            pasinger_id=passenger_id,
            seats_bookd=seats_requested,
            booking_status=False
        )
        db.session.add(booking)
        db.session.commit()
        flash("Foglalási igény elküldve! A sofőr jóváhagyása után válik megerősítetté.", "success")
    else:
        flash("Nincs elegendő szabad hely erre az útra.", "danger")
    
    return redirect(url_for('ride_details', trip_id=trip_id))

# --- ÚT MEGHIRDETÉSE ---
@app.route('/create-ride', methods=['GET', 'POST'])
def create_ride():
    if 'user_id' not in session:
        flash("Út meghirdetéséhez kérjük, jelentkezz be!", "warning")
        return redirect(url_for('login'))

    current_user_id = session['user_id']
    user = db.session.get(User, current_user_id)
    if not user:
        session.clear()
        flash("A munkamenet lejárt, kérjük jelentkezz be újra!", "warning")
        return redirect(url_for('login'))

    user_cars = Car.query.filter_by(owner_id=current_user_id).all()

    if request.method == 'POST':
        from_city = request.form.get('from', 'Marosvásárhely').strip()
        to_city = request.form.get('to', 'Kolozsvár').strip()
        departure_time_str = request.form.get('datetime')
        seats = request.form.get('seats')
        price = request.form.get('price')
        car_option = request.form.get('car_id')
        duration_raw = request.form.get('duration_minutes', '').strip()

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

        if duration_raw.isdigit() and int(duration_raw) > 0:
            dur_mins = int(duration_raw)
        else:
            dur_mins, _ = calculate_route_info(f_lat, f_lng, t_lat, t_lng)

        est_arrival_datetime = dep_datetime + timedelta(minutes=dur_mins)

        if car_option == 'new' or not user_cars:
            brand = request.form.get('new_brand', '').strip() or 'Egyedi'
            model = request.form.get('new_model', '').strip() or 'Model'
            color = request.form.get('new_color', '').strip() or 'Fekete'
            raw_plate = request.form.get('new_plate_num', '').strip()
            plate_num = raw_plate.replace(" ", "").replace("-", "").upper()

            if not plate_num:
                flash("Kérjük, add meg az autó rendszámát!", "danger")
                return render_template('create_ride.html', cars=user_cars)

            if len(plate_num) > 7:
                flash("A rendszám maximum 7 karakter hosszú lehet (pl. HR05XYZ)!", "danger")
                return render_template('create_ride.html', cars=user_cars)

            existing_car = Car.query.filter_by(plate_num=plate_num).first()

            if existing_car:
                car_id = existing_car.car_id
            else:
                new_car = Car(
                    owner_id=current_user_id,
                    brand=brand,
                    model=model,
                    color=color,
                    plate_num=plate_num,
                    seats=int(seats) if (seats and seats.isdigit()) else 4
                )
                try:
                    db.session.add(new_car)
                    db.session.commit()
                    car_id = new_car.car_id
                except IntegrityError:
                    db.session.rollback()
                    fallback_car = Car.query.filter_by(plate_num=plate_num).first()
                    if fallback_car:
                        car_id = fallback_car.car_id
                    else:
                        flash("Hiba történt az autó rögzítésekor (érvénytelen munkamenet vagy foglalt rendszám).", "danger")
                        return render_template('create_ride.html', cars=user_cars)
        else:
            car_id = int(car_option)

        new_trip = Trip(
            driver_id=current_user_id,
            car_id=car_id,
            start_city=from_city,
            destination_city=to_city,
            start_latitude=f_lat,
            start_longitude=f_lng,
            destination_latitude=t_lat,
            destination_longitude=t_lng,
            departure_time=dep_datetime,
            estimated_arival_time=est_arrival_datetime,
            price_per_seat=float(price) if price else 0.0,
            available_seats=int(seats) if (seats and seats.isdigit()) else 1
        )
        db.session.add(new_trip)
        db.session.commit()

        flash("Az utad sikeresen meghirdettük!", "success")
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
        phone = request.form.get('phone', '').strip() or None
        password = request.form.get('password', '')

        if not full_name or not email or not password:
            flash("Minden kötelező mezőt ki kell tölteni!", "danger")
            return render_template('register.html')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Ezzel az e-mail címmel már létezik fiók!", "warning")
            return render_template('register.html')

        new_user = User(full_name=full_name, email=email, password_hash=password, phone=phone)

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
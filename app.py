from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, Car, Trip, Booking, Review

app = Flask(__name__)

# XAMPP MySQL kapcsolódás
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ridewmy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLAlchemy inicializálása
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
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

# --- UTAZÁS RÉSZLETEI (RIDE DETAILS) ---
@app.route('/ride/<int:trip_id>')
def ride_details(trip_id):
    trip = db.session.get(Trip, trip_id)
    if not trip:
        return redirect(url_for('index'))

    formatted_date = trip.departure_time.strftime('%Y. %B %d.').lower() if trip.departure_time else "2026. október 25."
    start_hour = trip.departure_time.strftime('%H:%M') if trip.departure_time else "08:00"
    end_hour = trip.estimated_arival_time.strftime('%H:%M') if trip.estimated_arival_time else "10:15"

    car_name = f"{trip.car.brand} {trip.car.model} - {trip.car.color}" if trip.car else "Volkswagen Passat - Ezüst"

    ride_detail = {
        "id": trip.trip_id,
        "driver_name": trip.driver.full_name if trip.driver else "Szilárd T.",
        "rating": "5.0",
        "date_formatted": formatted_date,
        "from": "Kiindulás",
        "to": "Úticél",
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
    trip_id = int(request.form.get('trip_id'))
    seats_requested = int(request.form.get('seats', 1))
    
    passenger = User.query.filter(User.full_name.like('%Szilárd%')).first()
    passenger_id = passenger.user_id if passenger else 1

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

        if not departure_time_str or not departure_time_str.strip():
            flash("Kérjük, válassz ki egy indulási dátumot és időpontot!", "danger")
            user_cars = Car.query.filter_by(owner_id=current_user_id).all() or Car.query.all()
            return render_template('create_ride.html', cars=user_cars)

        try:
            dep_datetime = datetime.strptime(departure_time_str, '%Y-%m-%dT%H:%M')
        except (ValueError, TypeError):
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

        new_trip = Trip(
            driver_id=current_user_id, car_id=car_id,
            start_latitude=46.5425, start_longitude=24.5575,
            destination_latitude=46.7712, destination_longitude=23.6236,
            departure_time=dep_datetime, estimated_arival_time=dep_datetime,
            price_per_seat=float(price) if price else 0.0, available_seats=int(seats) if seats else 1
        )
        db.session.add(new_trip)
        db.session.commit()

        return redirect(url_for('index'))

    user_cars = Car.query.filter_by(owner_id=current_user_id).all() or Car.query.all()
    return render_template('create_ride.html', cars=user_cars)

if __name__ == '__main__':
    app.run(debug=True)
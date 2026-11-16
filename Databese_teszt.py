from datetime import datetime
from flask import Flask
from models import db, User, Car, Trip, Booking, Review

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ridewmy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        print("1. Adatbázis eldobása és újraépítése...")
        db.drop_all()
        db.create_all()

        print("\n2. Tesztadatok beszúrása...")
        user1 = User(full_name="Szilárd T.", email="szilard@ridewmy.hu", password_hash="password123")
        user2 = User(full_name="Kovács Anna", email="anna@ridewmy.hu", password_hash="password123")
        user3 = User(full_name="Nagy Péter", email="peter@ridewmy.hu", password_hash="password123")
        db.session.add_all([user1, user2, user3])
        db.session.commit()

        car1 = Car(owner_id=user1.user_id, brand="Volkswagen", model="Golf 7", color="Fekete", plate_num="MS10RDE", seats=4)
        car2 = Car(owner_id=user2.user_id, brand="Toyota", model="Prius", color="Fehér", plate_num="CJ22ABC", seats=4)
        db.session.add_all([car1, car2])
        db.session.commit()

        # Út 1: Marosvásárhely -> Kolozsvár
        trip1 = Trip(
            driver_id=user1.user_id, car_id=car1.car_id,
            start_city="Marosvásárhely", destination_city="Kolozsvár",
            start_latitude=46.5425, start_longitude=24.5575,
            destination_latitude=46.7712, destination_longitude=23.6236,
            departure_time=datetime(2026, 11, 20, 8, 0, 0),
            estimated_arival_time=datetime(2026, 11, 20, 10, 15, 0),
            price_per_seat=35.00, available_seats=3
        )

        # Út 2: Brassó -> Sepsiszentgyörgy (Valós koordinátákkal)
        trip2 = Trip(
            driver_id=user2.user_id, car_id=car2.car_id,
            start_city="Brassó", destination_city="Sepsiszentgyörgy",
            start_latitude=45.6579, start_longitude=25.6012,
            destination_latitude=45.8636, destination_longitude=25.7878,
            departure_time=datetime(2026, 11, 21, 14, 30, 0),
            estimated_arival_time=datetime(2026, 11, 21, 15, 15, 0),
            price_per_seat=25.00, available_seats=2
        )
        db.session.add_all([trip1, trip2])
        db.session.commit()

        booking1 = Booking(trip_id=trip1.trip_id, pasinger_id=user3.user_id, seats_bookd=1, booking_status=True)
        db.session.add(booking1)
        db.session.commit()

        review1 = Review(booking_id=booking1.booking_id, reviewer_id=user3.user_id, rating=5, comment="Szuper volt az út!")
        db.session.add(review1)
        db.session.commit()

        print("\n--- SIKERES FRISSÍTÉS ÉS ADATFELTÖLTÉS ---")
        print(f"Utak száma: {Trip.query.count()}")

    except Exception as e:
        print(f"HIBA: {e}")
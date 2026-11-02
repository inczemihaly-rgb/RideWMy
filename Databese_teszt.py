from datetime import datetime
from flask import Flask
from models import db, User, Car, Trip, Booking, Review

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ridewmy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        print("1. Előző adatok tisztítása...")
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0;"))
        Review.query.delete()
        Booking.query.delete()
        Trip.query.delete()
        Car.query.delete()
        User.query.delete()
        db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.session.commit()

        print("\n2. Tesztadatok rögzítése...")
        # Felhasználók
        user1 = User(full_name="Kovács Anna", email="anna@ridewmy.hu", password_hash="hash123")
        user2 = User(full_name="Nagy Péter", email="peter@ridewmy.hu", password_hash="hash456")
        db.session.add_all([user1, user2])
        db.session.commit()

        # Eltároljuk az első felhasználó ID-ját a tisztességes ID-alapú teszthez
        target_user_id = user1.user_id
        target_user_id2 = user2.user_id

        # Autó az első felhasználóhoz
        car = Car(
            owner_id=target_user_id, 
            brand="Toyota", model="Prius", color="Fehér", plate_num="ABC-123", seats=4
        )
        db.session.add(car)
        db.session.commit()

        # Utazás az első felhasználó által
        trip = Trip(
            driver_id=target_user_id, 
            car_id=car.car_id, 
            start_latitude=47.497913, start_longitude=19.040236, 
            destination_latitude=46.961389, destination_longitude=17.892500, 
            departure_time=datetime(2026, 6, 15, 10, 0, 0),
            price_per_seat=3500.00, available_seats=3,
            estimated_arival_time=datetime(2026, 6, 15, 12, 30, 0)
        )
        db.session.add(trip)
        db.session.commit()

        # Foglalás a második felhasználótól
        booking = Booking(
            trip_id=trip.trip_id, pasinger_id=user2.user_id, seats_bookd=2, booking_status=True
        )
        db.session.add(booking)
        db.session.commit()

        # Értékelés
        review = Review(
            booking_id=booking.booking_id, reviewer_id=user2.user_id, rating=5, comment="Szuper!"
        )
        db.session.add(review)
        db.session.commit()

        print("\n--- ÁLLAPOT TÖRLÉS ELŐTT ---")
        print(f"Felhasználók száma: {User.query.count()} (Várt: 2)")
        print(f"Autók száma:        {Car.query.count()} (Várt: 1)")
        print(f"Utak száma:         {Trip.query.count()} (Várt: 1)")
        print(f"Foglalások száma:   {Booking.query.count()} (Várt: 1)")
        print(f"Értékelések száma:  {Review.query.count()} (Várt: 1)")

        print(f"\n3. TESZT: Töröljük a felhasználót ID alapján (user_id = {target_user_id})...")
        
        # ID alapú lekérés és törlés a User modellből
        user_to_delete = db.session.get(User, target_user_id2)
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
            print("-> Felhasználó sikeresen törölve ID alapján!")
        else:
            print("-> A felhasználó nem található ezzel az ID-val.")

        print("\n--- ÁLLAPOT A FELHASZNÁLÓ TÖRLÉSE UTÁN (Kaszkád teszt) ---")
        print(f"Felhasználók száma: {User.query.count()} (Várt: 1 - csak a második user maradt)")
        print(f"Autók száma:        {Car.query.count()} (Várt: 0)")
        print(f"Utak száma:         {Trip.query.count()} (Várt: 0)")
        print(f"Foglalások száma:   {Booking.query.count()} (Várt: 0)")
        print(f"Értékelések száma:  {Review.query.count()} (Várt: 0)")

        print("\nSiker! Az ID szerinti felhasználó-törlés és a kaszkád mechanizmus lefutott!")

    except Exception as e:
        print(f"HIBA TÖRTÉNT: {e}")
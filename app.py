from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Car, Trip, Booking, Review

app = Flask(__name__)

# XAMPP MySQL kapcsolódás (root user, jelszó nélkül, localhost, ridewmy adatbázis)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ridewmy'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

if __name__ == '__main__':
    app.run(debug=True)
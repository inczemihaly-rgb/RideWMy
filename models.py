from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(55))
    
    # Kapcsolatok a többi táblával
    cars = db.relationship('Car', backref='owner', cascade='all, delete-orphan')
    trips = db.relationship('Trip', backref='driver', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='passenger', cascade='all, delete-orphan')


class Car(db.Model):
    __tablename__ = 'cars'
    
    car_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'))
    brand = db.Column(db.String(30))
    model = db.Column(db.String(30))
    color = db.Column(db.String(20))
    plate_num = db.Column(db.String(7), unique=True)
    seats = db.Column(db.Integer)
    
    trips = db.relationship('Trip', backref='car', cascade='all, delete-orphan')


class Trip(db.Model):
    __tablename__ = 'trips'
    
    trip_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'))
    car_id = db.Column(db.Integer, db.ForeignKey('cars.car_id', ondelete='CASCADE'))
    start_latitude = db.Column(db.Numeric(10, 8))
    start_longitude = db.Column(db.Numeric(11, 8))
    destination_latitude = db.Column(db.Numeric(10, 8))
    destination_longitude = db.Column(db.Numeric(11, 8))
    departure_time = db.Column(db.DateTime)
    price_per_seat = db.Column(db.Numeric(6, 2))
    available_seats = db.Column(db.Integer)
    estimated_arival_time = db.Column(db.DateTime)
    
    bookings = db.relationship('Booking', backref='trip', cascade='all, delete-orphan')


class Booking(db.Model):
    __tablename__ = 'bookings'
    
    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.trip_id', ondelete='CASCADE'))
    pasinger_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'))
    seats_bookd = db.Column(db.Integer)
    booking_status = db.Column(db.Boolean, default=True)
    creatid_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    
    reviews = db.relationship('Review', backref='booking', cascade='all, delete-orphan')


class Review(db.Model):
    __tablename__ = 'reviuws'  # Figyelve az eredeti elírásra
    
    reviuw_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.booking_id', ondelete='CASCADE'))
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'))
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
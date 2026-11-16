-- 1. Létrehozzuk a ridewmy adatbázist
CREATE DATABASE IF NOT EXISTS ridewmy;

-- 2. Kiválasztjuk használatra
USE ridewmy;

-- 3. Users tábla
CREATE TABLE IF NOT EXISTS users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(50),
  email VARCHAR(100) UNIQUE,
  password_hash VARCHAR(255)
);

-- 4. Cars tábla
CREATE TABLE IF NOT EXISTS cars (
  car_id INT AUTO_INCREMENT PRIMARY KEY,
  owner_id INT,
  brand VARCHAR(30),
  model VARCHAR(30),
  color VARCHAR(20),
  plate_num VARCHAR(7) UNIQUE,
  seats INT,
  FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 5. Trips tábla (start_city és destination_city hozzáadva)
CREATE TABLE IF NOT EXISTS trips (
  trip_id INT AUTO_INCREMENT PRIMARY KEY,
  driver_id INT,
  car_id INT,
  start_city VARCHAR(100) DEFAULT 'Kiindulás',
  destination_city VARCHAR(100) DEFAULT 'Úticél',
  start_latitude DECIMAL(10, 8),
  start_longitude DECIMAL(11, 8),
  destination_latitude DECIMAL(10, 8),
  destination_longitude DECIMAL(11, 8),
  departure_time DATETIME,
  price_per_seat DECIMAL(10, 2),
  available_seats INT,
  estimated_arival_time DATETIME,
  FOREIGN KEY (driver_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (car_id) REFERENCES cars(car_id) ON DELETE CASCADE
);

-- 6. Bookings tábla
CREATE TABLE IF NOT EXISTS bookings (
  booking_id INT AUTO_INCREMENT PRIMARY KEY,
  trip_id INT,
  pasinger_id INT,
  seats_bookd INT,
  booking_status BOOLEAN DEFAULT TRUE,
  creatid_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (trip_id) REFERENCES trips(trip_id) ON DELETE CASCADE,
  FOREIGN KEY (pasinger_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 7. Reviews tábla
CREATE TABLE IF NOT EXISTS reviuws (
  reviuw_id INT AUTO_INCREMENT PRIMARY KEY,
  booking_id INT,
  reviewer_id INT,
  rating INT CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (booking_id) REFERENCES bookings(booking_id) ON DELETE CASCADE,
  FOREIGN KEY (reviewer_id) REFERENCES users(user_id) ON DELETE CASCADE
);
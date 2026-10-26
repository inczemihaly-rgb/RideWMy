import requests
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Memóriabeli adattároló (később SQL adatbázis)
rides = [
    {
        "id": 1,
        "driver": "Szilárd T.",
        "rating": "4.9",
        "from": "Marosvásárhely",
        "to": "Kolozsvár",
        "price": "35 RON",
        "seats": "2 szabad hely",
        "startTime": "08:00",
        "endTime": "10:15",
        "fromLat": 46.5425,
        "fromLng": 24.5575,
        "toLat": 46.7712,
        "toLng": 23.6236
    }
]

def get_coords(city_name):
    """Automatikusan lekéri a város koordinátáit az OpenStreetMap Nominatim API-ból"""
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={city_name}&countrycodes=ro&limit=1"
        headers = {'User-Agent': 'RIDEWMY-App'}
        response = requests.get(url, headers=headers, timeout=3)
        data = response.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"Hiba a koordináta lekérésekor ({city_name}):", e)
    return None, None

@app.route('/')
def index():
    return render_template('index.html', rides=rides)

@app.route('/create-ride', methods=['GET', 'POST'])
def create_ride():
    if request.method == 'POST':
        from_city = request.form.get('from')
        to_city = request.form.get('to')
        
        # Automatikus koordináta lekérés a megadott városokhoz
        from_lat, from_lng = get_coords(from_city)
        to_lat, to_lng = get_coords(to_city)

        new_ride = {
            "id": len(rides) + 1,
            "driver": request.form.get('driver', 'Új Felhasználó'),
            "rating": "5.0",
            "from": from_city,
            "to": to_city,
            "price": f"{request.form.get('price', '30')} RON",
            "seats": f"{request.form.get('seats', '3')} szabad hely",
            "startTime": request.form.get('startTime', '09:00'),
            "endTime": request.form.get('endTime', '11:00'),
            "fromLat": from_lat,
            "fromLng": from_lng,
            "toLat": to_lat,
            "toLng": to_lng
        }
        
        rides.append(new_ride)
        return redirect(url_for('index'))
        
    return render_template('create_ride.html')

if __name__ == '__main__':
    app.run(debug=True)
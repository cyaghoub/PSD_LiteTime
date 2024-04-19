from flask import Flask, render_template, request, session, redirect, url_for
import requests
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to your secret key

SUNSET_API_URL = 'https://api.sunrise-sunset.org/json'
DATA_DIRECTORY = os.path.join(os.getcwd(), 'data')
DATABASE_FILE = os.path.join(DATA_DIRECTORY, 'users.txt')


def get_upcoming_friday():
    today = datetime.today().date()
    days_til_fri = (4 - today.weekday() + 7) % 7
    upcoming_fri = today + timedelta(days=days_til_fri)
    return upcoming_fri


def get_city_coordinates(city_name):
    geolocator = Nominatim(user_agent="LiteTime")
    location = geolocator.geocode(city_name)
    if location:
        return location.latitude, location.longitude, location.raw.get('timezone')
    else:
        return None, None, None


def load_users():
    users = {}
    try:
        with open(DATABASE_FILE, 'r') as file:
            for line in file:
                username, password, name, city = line.strip().split(',')
                users[username] = {'password': password, 'name': name, 'city': city}
    except FileNotFoundError:
        pass
    return users


def authenticate_user(username, password):
    users = load_users()
    if username in users and users[username]['password'] == password:
        return True
    return False


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate_user(username, password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error_message = 'Invalid username or password. Please try again.'
            return render_template('index.html', error_message=error_message)

    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))

    username = session['username']
    city = load_users()[username]['city']

    latitude, longitude, city_timezone = get_city_coordinates(city)
    if latitude is not None and longitude is not None:
        friday_date = get_upcoming_friday()
        formatted_date = friday_date.strftime('%Y-%m-%d')

        params = {'lat': latitude, 'lng': longitude, 'date': formatted_date, 'formatted': 0, 'tzid': city_timezone}
        response = requests.get(SUNSET_API_URL, params=params)
        data = response.json()

        sunset_time_iso = data['results']['sunset']
        sunset_time_obj = datetime.fromisoformat(sunset_time_iso)
        sunset_time = sunset_time_obj.strftime('%I:%M %p')

        candle_lighting_time_obj = sunset_time_obj - timedelta(minutes=18)
        candle_lighting_time = candle_lighting_time_obj.strftime('%I:%M %p')

        success_message = request.args.get('success_message')
        return render_template('index.html', username=username, city=city,
                               sunset_time=sunset_time, candle_lighting_time=candle_lighting_time,
                               friday_date=friday_date, success_message=success_message)

    else:
        error_message = "City not found. Please try again."
        return render_template('index.html', error_message=error_message)




@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

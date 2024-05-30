import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import requests
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import pytz
from timezonefinder import TimezoneFinder
from dateutil import parser

# Set up the application and database path
app = Flask(__name__)
app.secret_key = 'password'

# Set up SQLite database URI
db_path = os.path.join(app.root_path, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)

# Create tables if they do not exist
with app.app_context():
    db.create_all()
# API URL
SUNSET_API_URL = 'https://api.sunrise-sunset.org/json'

# Function to get upcoming Friday
def get_upcoming_friday():
    today = datetime.today().date()
    days_til_fri = (4 - today.weekday() + 7) % 7
    upcoming_fri = today + timedelta(days=days_til_fri)
    return upcoming_fri

# Function to get city coordinates
def get_city_coordinates(city_name):
    geolocator = Nominatim(user_agent="LiteTime")
    location = geolocator.geocode(city_name)
    if location:
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
        return location.latitude, location.longitude, timezone_str
    else:
        return None, None, None

# Index route for login and user listing
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check user credentials
        user = User.query.filter_by(username=username, password=password).first()
        print("Login attempt:", username, password, "Success:", bool(user))

        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error_message = 'Invalid username or password. Please try again.'
            return render_template('signin.html', error_message=error_message)

    # Fetch all users for display
    users = User.query.all()
    print("Users in the database:", users)

    return render_template('index.html', users=users)

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        city = request.form['city']

        # Print out the form field values for debugging
        print("Received Registration Data - Username:", username, "Password:", password, "Name:", name, "City:", city)

        user = User.query.filter_by(username=username).first()
        if user:
            error_message = 'Username already exists. Please choose a different username.'
            print(error_message)
            return render_template('register.html', error_message=error_message)
        else:
            new_user = User(username=username, password=password, name=name, city=city)
            db.session.add(new_user)
            db.session.commit()
            success_message = 'Registration successful! You can now log in.'
            print("New user added:", new_user)
            return render_template('signin.html', success_message=success_message)

    return render_template('register.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))

    username = session['username']
    user = User.query.filter_by(username=username).first()
    city = user.city

    latitude, longitude, city_timezone = get_city_coordinates(city)
    if latitude is not None and longitude is not None:
        friday_date = get_upcoming_friday()
        formatted_date = friday_date.strftime('%Y-%m-%d')

        if city_timezone:
            try:
                timezone = pytz.timezone(city_timezone)

                # Retrieve sunset time
                params = {
                    'lat': latitude,
                    'lng': longitude,
                    'date': formatted_date,
                    'formatted': 0  # to get the time in UTC in ISO 8601 format
                }
                response = requests.get(SUNSET_API_URL, params=params)
                data = response.json()
                sunset_time_iso = data['results']['sunset']
                sunset_time_obj = parser.isoparse(sunset_time_iso)
                sunset_time = sunset_time_obj.astimezone(timezone).strftime('%I:%M %p')

                # Calculate candle lighting time (18 minutes before sunset)
                candle_lighting_time_obj = sunset_time_obj - timedelta(minutes=18)
                candle_lighting_time = candle_lighting_time_obj.astimezone(timezone).strftime('%I:%M %p')
            except pytz.exceptions.UnknownTimeZoneError:
                error_message = f"Unknown timezone: {city_timezone}"
                return render_template('index.html', error_message=error_message)

            success_message = request.args.get('success_message')
            return render_template('index.html', username=username, city=city,
                                   sunset_time=sunset_time, candle_lighting_time=candle_lighting_time,
                                   friday_date=friday_date, success_message=success_message)
        else:
            error_message = "City timezone information not found. Please try again."
            return render_template('index.html', error_message=error_message)

    else:
        error_message = "City not found. Please try again."
        return render_template('index.html', error_message=error_message)

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database and tables
    app.run(debug=True)

from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim

app = Flask(__name__)

SUNSET_API_URL = 'https://api.sunrise-sunset.org/json'


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


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        city_name = request.form['city']
        latitude, longitude, city_timezone = get_city_coordinates(city_name)
        if latitude is not None and longitude is not None:
            friday_date = get_upcoming_friday()
            formatted_date = friday_date.strftime('%Y-%m-%d')

            params = {'lat': latitude, 'lng': longitude, 'date': formatted_date, 'formatted': 0, 'tzid': city_timezone}
            response = requests.get(SUNSET_API_URL, params=params)
            data = response.json()

            sunset_time_iso = data['results']['sunset']

            # Extracting only the time part
            sunset_time_obj = datetime.fromisoformat(sunset_time_iso)
            sunset_time = sunset_time_obj.strftime('%I:%M %p')

            # Calculating candle lighting time (18 minutes before sunset)
            candle_lighting_time_obj = sunset_time_obj - timedelta(minutes=18)
            candle_lighting_time = candle_lighting_time_obj.strftime('%I:%M %p')

            return render_template('index.html', sunset_time=sunset_time,
                                   candle_lighting_time=candle_lighting_time,
                                   friday_date=friday_date)
        else:
            error_message = "City not found. Please try again."
            return render_template('index.html', error_message=error_message)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

SUNSET_API_URL = 'https://api.sunrise-sunset.org/json'

def get_upcoming_friday():
    #todays date
    today = datetime.today().date()

    #calc days til fri, aka "4"
    days_til_fri = (4 - today.weekday()+7) % 7

    #date for upcoming friday
    upcoming_fri = today  + timedelta(days=days_til_fri)

    return upcoming_fri


@app.route('/')
def index():

    friday_date = get_upcoming_friday()

    #format date as string for api in YYYY-MM-DD
    formatted_date = friday_date.strftime('%Y-%m-%d')

    #example of nyc coordinates and timezoneid
    latitude = 40.7128
    longitude = -74.0060

    tzid = 'America/New_York'

    #request to sunset api WITH upcoming friday date
    params = {'lat': latitude, 'lng': longitude, 'date': formatted_date, 'tzid': tzid}
    response = requests.get(SUNSET_API_URL, params=params)
    data = response.json()

    #display response(sunset time)
    sunset_time = data['results']['sunset']

    return render_template('index.html', sunset_time=sunset_time, friday_date=friday_date)

if __name__ == '__main__':
    app.run(debug=True)

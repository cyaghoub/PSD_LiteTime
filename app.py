from flask import Flask, render_template
import requests

app = Flask(__name__)

SUNSET_API_URL = 'https://api.sunrise-sunset.org/json'

@app.route('/')
def index():
    #example of nyc coordinates
    latitude = 40.7128
    longitude = -74.0060

    #request to sunset api
    params = {'lat': latitude, 'lng': longitude}
    response = requests.get(SUNSET_API_URL, params=params)
    data = response.json()

    #display response(sunset time)
    sunset_time = data['results']['sunset']

    return render_template('index.html', sunset_time=sunset_time)

if __name__ == '__main__':
    app.run(debug=True)

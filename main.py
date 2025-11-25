import requests, json, sys, os
from pprint import pprint
from flask import Flask, render_template, redirect, request
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import SelectField
from page_data import pages

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
bootstrap = Bootstrap5(app)

API_KEY_WEATHER = "c1dc9ea9c2388bec9e6448061862dbb4"
def get_lat_lon(city_name):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={API_KEY_WEATHER}"
    response = requests.get(geo_url)
    data = response.json()

    if data:
        return data[0]['lat'], data[0]['lon'], data[0]['name']
    else:
        return None, None, None

class PageSelection(FlaskForm):
    chosen_page = SelectField( 
    choices=[('null','Choose a page')] + ([(route, page) for page, route in pages.items()]),
    )

@app.route('/', methods=('GET', 'POST'))
def main():

    form = PageSelection()

    if form.validate_on_submit() and form.chosen_page.data != 'null': 
        return redirect(f'/{form.chosen_page.data}')

    return render_template('main.html', form = form)

@app.route('/weather', methods=['GET', 'POST'])
def weather():
    weather_data = None
    city = "Seaside"

    if request.method == 'POST':
        city = request.form.get('city_input')
    lat, lon, location_name = get_lat_lon(city)

    if lat and lon:
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY_WEATHER}&units=imperial"
        response = requests.get(weather_url)
        api_data = response.json()

        weather_data = {
            'location': location_name,
            'temp': round(api_data['main']['temp']),
            'description': api_data['weather'][0]['description'].title(),
            'icon': api_data['weather'][0]['icon']
        }
    return render_template('weather.html', weather=weather_data)

@app.route('/test')
def test():
    return render_template("test.html")

@app.route('/example')
def example():
    return render_template("example.html")

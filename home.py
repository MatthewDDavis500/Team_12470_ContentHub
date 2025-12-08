from flask import render_template, request
import requests

API_KEY = "c1dc9ea9c2388bec9e6448061862dbb4"

def get_lat_lon(city_name):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={API_KEY}"
    response = requests.get(geo_url)
    data = response.json()

    if data:
        return data[0]['lat'], data[0]['lon'], data[0]['name']
    else:
        return None, None, None

def weather():
    weather_data = None
    if request.method == 'POST':
        city = request.form.get('city_input')
        if city:
            lat, lon, name = get_lat_lon(city)
            if lat and lon:
                weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=imperial"
                response = requests.get(weather_url)
                api_data = response.json()
                
                weather_data = {
                    "location": name,
                    "temp": round(api_data['main']['temp']),
                    "description": api_data['weather'][0]['description'].title(),
                    "icon": api_data['weather'][0]['icon']
                }

    return render_template('weather.html', weather=weather_data)
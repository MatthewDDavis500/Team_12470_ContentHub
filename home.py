from flask import render_template, request
import requests

WEATHER_API_KEY = "c1dc9ea9c2388bec9e6448061862dbb4"
NEWS_API_KEY = "pub_9c4133f710334b22825d2481d31ad50e"

def get_lat_lon(city_name):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={WEATHER_API_KEY}"
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
                weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=imperial"
                response = requests.get(weather_url)
                api_data = response.json()
                
                weather_data = {
                    "location": name,
                    "temp": round(api_data['main']['temp']),
                    "description": api_data['weather'][0]['description'].title(),
                    "icon": api_data['weather'][0]['icon']
                }

    return render_template('weather.html', weather=weather_data)

def get_news_data(query = "breaking news"):
    base_url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": NEWS_API_KEY,
        "q": query,
        "language": "en", 
        "image": 1        
    }

    try:
        response = requests.get(base_url, params=params)
        data = response.json()

        if response.status_code == 200 and 'results' in data:
            return data['results']
        else:
            return None
    except Exception as e:
        print(f"Error fetching news: {e}")
        return None

def news():
    articles = []
    search_term = "Technology" 

    if request.method == 'POST':
        user_input = request.form.get('news_input')
        if user_input:
            search_term = user_input

    raw_articles = get_news_data(search_term)

    if raw_articles:
        for item in raw_articles[:5]: 
            articles.append({
                "title": item.get('title'),
                "link": item.get('link'),
                "description": item.get('description'),
                "image": item.get('image_url')
            })

    return render_template('news.html', articles=articles, search_term=search_term)
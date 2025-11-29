import requests
import random
import time
import os
from dotenv import load_dotenv

load_dotenv()

# IMPORTANT: This is how I'm buidling widgets. This should allow for relitively easy widget creation/additions.
# WIDGET REGISTRY SYSTEM
# ====================================================
#  This file is where we define all our widgets.
#  You do NOT need to touch the database files or HTML to add a new widget.
#
#  HOW TO ADD A NEW WIDGET:
#  1. Write two python functions:
#     - *_summary(settings): Returns the data for the small dashboard box.
#     - *_detail(settings): Returns the data for the full details page.
#  2. Add your widget to the WIDGET_REGISTRY dictionary at the bottom.
#  3. (Optional) If your widget needs user input (like a city name), 
#     add it to the 'config' section in the registry.


# CACHING SYSTEM (This is meant to reduce API calls and speed up the app a bit by storing data in memory for a short time)

CACHE = {}
CACHE_DURATION = 300  # Keep data for 300 seconds (5 minutes)


def fetch_with_cache(url):
    current_time = time.time()

    # 1. Check if we have valid data in memory
    if url in CACHE:
        data, timestamp = CACHE[url]
        if current_time - timestamp < CACHE_DURATION:
            # Data is fresh! Return immediately (Instant)
            return data

    # 2. Data is old or missing. Fetch from API.
    #  use a very short timeout (0.5s). If the API is slow, then have the function give up
    # instead of freezing the webpage.
    print(f">> Fetching fresh data from: {url}")
    try:
        response = requests.get(url, timeout=0.5)
        if response.status_code == 200:
            json_data = response.json()
            # Save to cache
            CACHE[url] = (json_data, current_time)
            return json_data
    except:
        pass  # Fall through to the error raise below

    raise Exception("API Timeout or Error")



# HELPER: SAFE GET SETTINGS
# Helper function: Safely gets a user setting (like 'city' or 'username').
# It handles capitalization differences automatically.
def get_setting(settings, key, default):
    if not settings:
        return default
    # Try exact match
    if key in settings:
        return settings[key]
    # Try lowercase match
    for k, v in settings.items():
        if k.lower() == key.lower():
            return v
    return default

# WIDGET 1: BITCOIN (No Config needed -- this means no user settings are needed, nothing that would modify the API call)
# ====================================================
"""
    The 'Summary' function controls the small widget box on the dashboard.
    It must return a dictionary with:
    - 'text': The main text to display
    - 'image': An optional URL for an icon/image (can be empty string if none)
"""
def crypto_summary(settings):
    url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    btc_logo = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Bitcoin.svg/128px-Bitcoin.svg.png"
    try:
        # USE CACHE: Crypto doesn't need to update every second
        data = fetch_with_cache(url)
        price = float(data['data']['amount'])
        return {"text": f"${price:,.2f}", "image": btc_logo}
    except:
        return {"text": "Loading...", "image": btc_logo}



"""
    The 'Detail' function controls the page when you click 'View Details'.
    It returns a dictionary. Every Key/Value pair will be listed on the page.
"""
def crypto_details(settings):
    url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    try:
        data = fetch_with_cache(url)
        price = float(data['data']['amount'])
        return {
            "Cryptocurrency": "Bitcoin (BTC)",
            "Current Price": f"${price:,.2f}",
            "Source": "Coinbase Public API"
        }
    except:
        return {"Status": "Could not load details"}


# WIDGET 2: POKEMON RANDOMIZER (This one doesn't use config)
# ====================================================

def pokemon_summary(settings):
    # We DO NOT cache this, because we want it to change every time (i.e. randomize)
    poke_id = random.randint(1, 151)
    url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
    try:
        response = requests.get(url, timeout=0.5)
        data = response.json()
        name = data['name'].capitalize()
        image = data['sprites']['front_default']
        return {"text": f"It's {name}!", "image": image}
    except:
        return {"text": "Wild Pokemon fled!", "image": ""}


def pokemon_details(settings):
    poke_id = random.randint(1, 151)
    url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
    try:
        response = requests.get(url, timeout=0.5)
        data = response.json()
        types = ", ".join([t['type']['name'] for t in data['types']]).title()
        return {
            "Name": data['name'].capitalize(),
            "ID": f"#{data['id']}",
            "Types": types
        }
    except:
        return {"Error": "Wild Pokemon fled!"}


# WIDGET 3: WEATHER (This one uses user config to set the city, or defaults to a specific city, I chose Salinas)
# ====================================================
def weather_summary(settings):
    city = get_setting(settings, 'city', 'Salinas')

    api_key = os.getenv("WEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"

    try:
        data = fetch_with_cache(url)

        if data.get('cod') != 200:
            return {"text": "City Not Found", "image": ""}

        temp = round(data['main']['temp'])
        icon_code = data['weather'][0]['icon']
        icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"

        return {
            "text": f"{city}: {temp}°F",
            "image": icon_url
        }
    except:
        return {"text": "Weather Error", "image": ""}


def weather_details(settings):
    city = get_setting(settings, 'city', 'Salinas')
    api_key = os.getenv("WEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"

    try:
        data = fetch_with_cache(url)
        return {
            "Location": f"{data['name']}, {data['sys']['country']}",
            "Temperature": f"{data['main']['temp']}°F",
            "Condition": data['weather'][0]['description'].title(),
            "Wind Speed": f"{data['wind']['speed']} mph"
        }
    except:
        return {"Error": "Could not fetch weather"}


# WIDGET 4: POKEMON SEARCH (This one uses user config to set the target pokemon to search for)
# If no pokemon is specified, it defaults to "Pikachu"
# ====================================================


def poke_search_summary(settings):
    target = get_setting(settings, 'target_pokemon', 'pikachu').lower()
    url = f"https://pokeapi.co/api/v2/pokemon/{target}"

    try:
        data = fetch_with_cache(url)
        name = data['name'].capitalize()
        image = data['sprites']['front_default']

        return {
            "text": f"Tracking: {name}",
            "image": image
        }
    except:
        return {"text": "Not Found", "image": ""}


def poke_search_detail(settings):
    target = get_setting(settings, 'target_pokemon', 'pikachu').lower()
    url = f"https://pokeapi.co/api/v2/pokemon/{target}"

    try:
        data = fetch_with_cache(url)
        types = ", ".join([t['type']['name'] for t in data['types']]).title()

        return {
            "Name": data['name'].capitalize(),
            "ID": f"#{data['id']}",
            "Types": types,
            "Stats": "User Selected"
        }
    except:
        return {"Error": "Could not load details"}


# THE REGISTRY
#  This dictionary tells the app which widgets exist.
# ====================================================
WIDGET_REGISTRY = {
    "Bitcoin Tracker": {
        "summary": crypto_summary,
        "detail": crypto_details,
        "config": {} # Empty dict = No user settings needed
    },
    "Pokemon Randomizer": {
        "summary": pokemon_summary,
        "detail": pokemon_details,
        "config": {}
    },
    "Weather": {
        "summary": weather_summary,
        "detail": weather_details,
        "config": {
            # Adding a key here AUTOMATICALLY creates a form input for the user!
            # Format: "Label Name": "Default Value"
            "city": "Salinas"
        }
    },
    "Pokemon Search": {
        "summary": poke_search_summary,
        "detail": poke_search_detail,
        "config": {
            "target_pokemon": "pikachu"
        }
    }
}

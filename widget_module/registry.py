import requests
import random
import time
import os
import tempfile
from dotenv import load_dotenv
from PIL import Image
from markupsafe import Markup

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
        if url[:27] == 'https://gutendex.com/books?':
            # Gutendex API needs a little more time to fetch from large library of books
            response = requests.get(url, timeout=2.0)
        else:
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


# WIDGET 5: BOOK SEARCH (User config to set the search term to use)
# If no previous searches, defaults to empty search
# ====================================================


def book_search_summary(settings):
    term = get_setting(settings, 'Search', 'N/A')
    image = '../static/images/book_search_image.jpg'

    return {
        "text": f"Last Search: {term}",
        "image": image
    }


def book_search_detail(settings):
    term = get_setting(settings, 'search', '').lower().replace(' ', '%20')
    url = f"https://gutendex.com/books?search={term}&languages=en"

    try:
        data = fetch_with_cache(url)

        detail_result = {
            "Total Number of Search Results": data['count']
        }

        for i, book in enumerate(data['results']):
            author_string = ''
            for j, author in enumerate(book['authors']):
                # format name
                name = author['name']
                name = name[(name.find(',') + 2):] + ' ' + name[:(name.find(','))]
                
                # add to string of authors
                if j < len(book['authors']) - 1:
                    author_string = author_string + name + ', '
                else:
                    author_string = author_string + name
            
            book_details = {
                f"Result {i+1}": '#line_break#',
                f"({i+1}) Title": book['title'],
                f"({i+1}) Authors": author_string,
                f"({i+1}) Download Count": book['download_count']
            }
            detail_result.update(book_details)

        return detail_result
    except:
        return {"Error": "Search Failed."}

def player_summary(settings):
    try:
        return{ "text": "MiniPlayer", "image": '../static/images/spoty.png'}
    except:
        return{"text": "Player Error"}
def player_details(settings):
    try:
        return {
            "Launch Player": Markup(
                '<a href="/topsongs"><button style="padding:10px 20px;">Open</button></a>'
            )
        }
    except:
        return {"text": "Error"}
        
def image_filter_summary(settings):
    try:
        return {"text": "Image Filter", "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Pencil_edit_icon.svg/640px-Pencil_edit_icon.svg.png"}
    except:
        return {"text": "Image Load Error", "image": ""}

def image_filter_detail(settings):
    try:
        print (settings)
        filter_type = get_setting(settings, 'filter', 'None')
        file_path = get_setting(settings, 'image', 'static/images/penguin.jpg')
        im = Image.open(file_path)
        filtered_im = apply_filter(im.copy(), filter_type)
        filtered_im.save('static/uploads/filtered_image.png', format='PNG')
        return {
            "Filter Applied": filter_type,
            "img_Original Image": f'../{file_path}',
            "img_Filtered Image": '../static/uploads/filtered_image.png'
        }
    except:
        return {"Error": "Could not process image"}

def apply_filter(im, filter_type):

    if filter_type == 'grayscale':
        filter_list = [((p[0]*299 + p[1]*587 + p[2]*114 )//1000, ) * 3 for p in im.getdata()]
        im.putdata(filter_list)
    elif filter_type == 'negative':
        filter_list = [(255 - p[0], 255 - p[1], 255 - p[2]) for p in im.getdata()]
        im.putdata(filter_list)
    elif filter_type == 'sepia':
        filter_list = []
        for p in im.getdata():
            r,g,b = p[0], p[1], p[2];
            if r < 63:
                r *= 1.1
                b *= 0.9
            elif r > 62 and r < 192:
                r *= 1.15
                b *= 0.85
            else:
                r *= 1.08
                b *= 0.5
            filter_list.append((int(r),int(g),int(b)))
        im.putdata(filter_list)
    return im

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
    },
    "Book Search": {
        "summary": book_search_summary,
        "detail": book_search_detail,
        "config": {
            "search": "N/A"
        }
    },
    "Image Filtering": {
        "summary": image_filter_summary,
        "detail": image_filter_detail,
        "config": {
            "select_filter": ["grayscale", "negative", "sepia"],
            "upload_image": ""
        }
    },
    "MiniPlayer": {
    "summary": player_summary,
    "detail": player_details,
    "config": {}  
    } 
}

from flask import session, has_request_context
import requests
import random
import time
import os
import tempfile
from dotenv import load_dotenv
from PIL import Image
from markupsafe import Markup
from helper_functions.pokemon import format_pokemon_data
from helper_functions.crypto import format_crypto_data

load_dotenv()

CACHE = {}
CACHE_DURATION = 300

USER_ARTICLES = {}

def fetch_with_cache(url):
    current_time = time.time()

    if url in CACHE:
        data, timestamp = CACHE[url]
        if current_time - timestamp < CACHE_DURATION:
            return data
        
    print(f">> Fetching fresh data from: {url}")
    try:
        if url[:27] == 'https://gutendex.com/books?':
            response = requests.get(url, timeout=2.0)
        else:
            response = requests.get(url, timeout=0.5)


        if response.status_code == 200:
            json_data = response.json()
            # Save to cache
            CACHE[url] = (json_data, current_time)
            return json_data
    except:
        pass

    raise Exception("API Timeout or Error")



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
    print(f'default {default}')
    return default


def crypto_summary(settings):
    url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    btc_logo = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Bitcoin.svg/128px-Bitcoin.svg.png"
    try:
        data = fetch_with_cache(url)
        price = float(data['data']['amount'])
        return {"text": f"${price:,.2f}", "image": btc_logo}
    except:
        return {"text": "Loading...", "image": btc_logo}



def crypto_details(settings):
    url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    try:
        data = fetch_with_cache(url)
        
        return format_crypto_data(data)
    except Exception as e:
        print(f"Crypto Error: {e}")
        return {"Error": "Could not load details"}


def pokemon_summary(settings):
    poke_id = random.randint(1, 151)

    if 'instance_id' in settings:
        session_key = f"poke_randomizer_{settings['instance_id']}"
        session[session_key] = poke_id
        
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
    poke_id = None

    if 'instance_id' in settings:
        session_key = f"poke_randomizer_{settings['instance_id']}"
        poke_id = session.get(session_key)
    
    if not poke_id:
        poke_id = random.randint(1, 151)
    
    url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
    try:
        response = requests.get(url, timeout=0.5)
        data = response.json()
        return format_pokemon_data(data)
    except Exception as e:
        print(f"Pokemon Error: {e}")
        return {"Error": "Wild Pokemon fled!"}


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

        return format_pokemon_data(data)
    except:
        return {"Error": "Could not load details"}


# WIDGET 5: BOOK SEARCH (User config to set the search term to use)
# If no previous searches, defaults to empty search
# ====================================================

def book_search_summary(settings):
    term = get_setting(settings, 'search', 'N/A')
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
                '<a href="/music_login" target="_blank">'
                '<button style="padding:10px 20px; background-color:#1DB954; color:white; border:none; border-radius:12px;">Open</button>'
                '</a>'
            )
        }
    except:
        print("Error generating")
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
            r,g,b = p[0], p[1], p[2]
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

def news_summary(settings):
    country = get_setting(settings, 'country', 'us')
    api_key = os.getenv("NEWS_API_KEY")
    url = f"https://newsdata.io/api/1/news?apikey={api_key}&country={country}&language=en"

    try:
        data = fetch_with_cache(url)
        if data.get('status') != 'success':
            return {"text": "API Error", "image": ""}

        if data.get('results'):
            valid_stories = [a for a in data['results'] if a.get('title')]
            if not valid_stories:
                return {"text": "No Headlines", "image": ""}

            raw_article = random.choice(valid_stories)
            user_id = settings.get('user_id')

            if user_id:
                USER_ARTICLES[user_id] = raw_article.get('link')
            
            desc = raw_article.get('description')
            if not desc:
                desc = raw_article.get('content')
            if not desc:
                desc = "No description available. Click the link to read more."
            
            if len(str(desc)) > 350:
                desc = str(desc)[:347] + "..."

            image = raw_article.get('image_url')
            if image and len(image) > 250: 
                image = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Circle-icons-news.svg/512px-Circle-icons-news.svg.png"
            elif not image:
                image = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Circle-icons-news.svg/512px-Circle-icons-news.svg.png"

            title = raw_article['title']
            if len(title) > 100:
                title = title[:97] + "..."
            return {"text": title, "image": image}
        
        else:
            return {"text": "No News Found", "image": ""}
            
    except Exception as e:
        if "outside of request context" not in str(e):
            print(f"News Summary Error: {e}")
        return {"text": "Connection Error", "image": ""}


def news_detail(settings):
    country = get_setting(settings, 'country', 'us')
    api_key = os.getenv("NEWS_API_KEY")
    url = f"https://newsdata.io/api/1/news?apikey={api_key}&country={country}&language=en"

    try:
        data = fetch_with_cache(url)
        if data.get('results'):
            valid_stories = [a for a in data['results'] if a.get('title')]
            if not valid_stories:
                 return {"Error": "No articles found."}

            target_link = None
            if has_request_context() and 'user_id' in session:
                target_link = USER_ARTICLES.get(session['user_id'])

            found_article = None
            if target_link:
                for story in valid_stories:
                    if story.get('link') == target_link:
                        found_article = story
                        break
            
            # This is a fallback in case the specific article is not found (any reason)
            if not found_article:
                found_article = valid_stories[0]

            desc = found_article.get('description')
            if not desc:
                desc = found_article.get('content')
            if not desc:
                desc = "No description available. Click the link to read more."

            if len(str(desc)) > 300:
                desc = str(desc)[:300] + "..."

            return {
                "Headline": found_article['title'],
                "Date": found_article.get('pubDate', 'Unknown'),
                "Source": found_article.get('source_id', 'News').title(),
                "Description": desc,
                "Link": found_article.get('link', '#')
            }
        else:
            return {"Error": "No news data found"}
            
    except Exception as e:
        print(f"News Detail Error: {e}")
        return {"Error": "Could not fetch news details"}
    

# WIDGET 8: Is This My Card? (User config for guessing a card and storing score)
# ====================================================


def card_guess_summary(settings):
    rank = get_setting(settings, 'rank', '')
    suit = get_setting(settings, 'suit', '')
    image = '../static/images/card_guess_image.png'

    if rank != '' and suit != '':
        return {
            "text": f"Current Guess: {rank} of {suit}",
            "image": image
        }
    else:
        return {
            "text": f"No Current Guess",
            "image": image
        }

def card_guess_detail(settings):
    rank = get_setting(settings, 'rank', '')
    suit = get_setting(settings, 'suit', '')
    url = f"https://deckofcardsapi.com/api/deck/new/draw/?count=1"

    if rank != '' and suit != '':
        try:
            response = requests.get(url, timeout=0.5)
            if response.status_code != 200:
                return {"Error": "Dealer not letting go of your card..."}
            data = response.json()

            if not data['success']:
                return {"Error": "Dealer forgot the deck at home."}

            if (data['cards'][0]['value'] == rank) and (data['cards'][0]['suit'] == suit):
                print('Correct Guess')
                print('Score Incrememented')
                return {
                    f"YES, that WAS your card!": '#line_break#',
                    "img_": data['cards'][0]['image'],
                    "Your Card": f'{data['cards'][0]['value']} of {data['cards'][0]['suit']}',
                    "Your Guess": f'{rank} of {suit}'
                }
            else:
                print('Incorrect Guess')
                print('Score Decrememented')
                return {
                    f"NO, that was NOT your card!": '#line_break#',
                    "img_": data['cards'][0]['image'],
                    "Your Card": f'{data['cards'][0]['value']} of {data['cards'][0]['suit']}',
                    "Your Guess": f'{rank} of {suit}'
                }
        except:
            return {"Error": "Dealer is playing '52 Card Pickup'."}
    else:
        return {
            f"Please make a guess in the config menu.": '#line_break#'
        }


# THE REGISTRY
#  This dictionary tells the app which widgets exist.
# ====================================================
WIDGET_REGISTRY = {
    "Bitcoin Tracker": {
        "summary": crypto_summary,
        "detail": crypto_details,
        "config": {}
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
    },
    "News Feed": {
        "summary": news_summary,
        "detail": news_detail,
        "config": {
            "country": "us"
        }
    },
    "Is This My Card?": {
        "summary": card_guess_summary,
        "detail": card_guess_detail,
        "config": {
            "note_title": "Please make a guess here:",
            "select_rank": [
                "ACE",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "JACK",
                "QUEEN",
                "KING"
            ],
            "select_suit": [
                "CLUBS",
                "DIAMONDS",
                "SPADES",
                "HEARTS"
            ]
        }
    }
}

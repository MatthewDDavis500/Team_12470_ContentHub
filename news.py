from flask import Flask, render_template, request
import requests
from flask_bootstrap import Bootstrap5
app = Flask(__name__)
bootstrap = Bootstrap5(app)

NEWS_API_KEY = "pub_9c4133f710334b22825d2481d31ad50e"

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
from flask import Flask, render_template, redirect, request, session
import requests, base64

app = Flask(__name__)
app.secret_key = "your_secret_key"

CLIENT_ID = "8cb539019c48459192299f633e81346d"
CLIENT_SECRET = "99851631079b4f9b8b69c91c0f18b18e"
REDIRECT_URI = "http://127.0.0.1:5000/callback"

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

TOP_TRACKS = [
    "3n3Ppam7vgaVa1iaRUc9Lp",
    "7qiZfU4dY1lWllzX7mPBI3",
    "2takcwOaAZWiXQijPHIx7B",
    "1uNFoZAHBGtllmzznpCI3s",
    "0VjIjW4GlUZAMYd2vXMi3b"
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    scope = "user-read-private user-read-email"
    auth_url = (
        f"{SPOTIFY_AUTH_URL}?client_id={CLIENT_ID}"
        f"&response_type=code&redirect_uri={REDIRECT_URI}"
        f"&scope={scope}"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    token_resp = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data).json()
    session["access_token"] = token_resp.get("access_token")
    return redirect("/topsongs")

@app.route("/topsongs", methods=["GET", "POST"])
def topsongs():
    token = session.get("access_token")
    if not token:
        return redirect("/")

    headers = {"Authorization": f"Bearer {token}"}
    results = None

    # If the user submitted a search
    if request.method == "POST":
        query = request.form.get("query", "")
        if query:
            params = {"q": query, "type": "track", "limit": 10}
            results = requests.get(f"{SPOTIFY_API_BASE}/search", headers=headers, params=params).json()

    top_tracks = []
    if not results:
        TOP_TRACKS = [
            "0je57Uq5eTk1wrPzn9sWbl",
            "3yWuTOYDztXjZxdE2cIRUa",
            "2plbrEY59IikOBgBGLjaoe",
            "2X3DlOF546VuOJLPu7hn9J",
            "6CcmabfR68aD0jtjSVS8sy"
        ]
        track_ids = ",".join(TOP_TRACKS)
        resp = requests.get(f"{SPOTIFY_API_BASE}/tracks?ids={track_ids}", headers=headers).json()
        top_tracks = [t for t in resp.get("tracks", []) if t and t.get("album") and t["album"].get("images")]

    return render_template("topsongs.html", results=results, top_tracks=top_tracks)


@app.route("/player/<spotify_id>")
def player(spotify_id):
    token = session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    track_data = requests.get(f"{SPOTIFY_API_BASE}/tracks/{spotify_id}", headers=headers).json()

    embed_url = f"https://open.spotify.com/embed/track/{spotify_id}"

    return render_template(
        "player.html",
        embed_url=embed_url,
        track_name=track_data.get("name"),
        track_artist=track_data["artists"][0]["name"],
        track_image=track_data["album"]["images"][0]["url"]
    )

@app.route("/search", methods=["GET", "POST"])
def search():
    token = session.get("access_token")
    if not token:
        return redirect("/")

    results = None
    if request.method == "POST":
        query = request.form["query"]
        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": query, "type": "track", "limit": 10}
        results = requests.get(f"{SPOTIFY_API_BASE}/search", headers=headers, params=params).json()
    return render_template("search.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)

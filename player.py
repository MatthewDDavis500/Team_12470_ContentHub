from flask import Flask, render_template, redirect, request, session
import requests, base64

client_id = "8cb539019c48459192299f633e81346d"
client_secret = "99851631079b4f9b8b69c91c0f18b18e"
redirect_url = "http://127.0.0.1:5000/callback"

author = "https://accounts.spotify.com/authorize"
token_url = "https://accounts.spotify.com/api/token"
api_base = "https://api.spotify.com/v1"

#@app.route("/")
def index():
    return render_template("index.html")

#@app.route("/login")
def music_login():
    scope = "user-read-private user-read-email"
    auth_url = (
        f"{author}?client_id={client_id}"
        f"&response_type=code&redirect_uri={redirect_url}"
        f"&scope={scope}"
    )
    return redirect(auth_url)

#@app.route("/callback")
def callback():
    code = request.args.get("code")
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_url
    }
    token_resp = requests.post(token_url, headers=headers, data=data).json()
    session["access_token"] = token_resp.get("access_token")
    return redirect("/topsongs")

#@app.route("/topsongs", methods=["GET", "POST"])
def topsongs():
    token = session.get("access_token")
    if not token:
        return redirect("/music_login")

    headers = {"Authorization": f"Bearer {token}"}
    results = None

   
    if request.method == "POST":
        query = request.form.get("query", "")
        if query:
            params = {"q": query, "type": "track", "limit": 10}
            results = requests.get(f"{api_base}/search", headers=headers, params=params).json()

    top_tracks = []
    if not results:
        top = [
            "0je57Uq5eTk1wrPzn9sWbl",
            "3yWuTOYDztXjZxdE2cIRUa",
            "2plbrEY59IikOBgBGLjaoe",
            "2X3DlOF546VuOJLPu7hn9J",
            "6CcmabfR68aD0jtjSVS8sy"
        ]
        track_ids = ",".join(top)
        resp = requests.get(f"{api_base}/tracks?ids={track_ids}", headers=headers).json()
        top_tracks = [t for t in resp.get("tracks", []) if t and t.get("album") and t["album"].get("images")]

    return render_template("topsongs.html", results=results, top_tracks=top_tracks)


#@app.route("/player/<spotify_id>")
def player(spotify_id):
    token = session.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    track_data = requests.get(f"{api_base}/tracks/{spotify_id}", headers=headers).json()

    embed_url = f"https://open.spotify.com/embed/track/{spotify_id}"

    return render_template(
        "player.html",
        embed_url=embed_url,
        track_name=track_data.get("name"),
        track_artist=track_data["artists"][0]["name"],
        track_image=track_data["album"]["images"][0]["url"]
    )

#@app.route("/search", methods=["GET", "POST"])
def search():
    token = session.get("access_token")
    if not token:
        return redirect("/")

    results = None
    if request.method == "POST":
        query = request.form["query"]
        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": query, "type": "track", "limit": 10}
        results = requests.get(f"{api_base}/search", headers=headers, params=params).json()
    return render_template("search.html", results=results)




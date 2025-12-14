import importlib, requests, json, sys, os
from pprint import pprint
from flask import Flask, render_template, redirect, request, session, flash
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, PasswordField, validators
from page_data import pages

import db_connect
from widget_module.db import ( login_user, signup_user, get_available_widgets, add_widget_to_user, get_user_dashboard, get_widget_detail_data, sync_widgets, get_widget_config_fields, save_widget_settings, get_widget_settings)
from widget_module.registry import WIDGET_REGISTRY

conn = db_connect.get_db_connection()
sync_widgets(conn)
conn.close()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
bootstrap = Bootstrap5(app)

import player  
app.add_url_rule("/topsongs", view_func=player.topsongs, methods=["GET", "POST"])
app.add_url_rule("/music_login", view_func=player.music_login)
app.add_url_rule("/callback", view_func=player.callback)
app.add_url_rule("/play/<spotify_id>", view_func=player.play)
app.add_url_rule("/search", view_func=player.search, methods=["GET", "POST"])


API_KEY_WEATHER = "c1dc9ea9c2388bec9e6448061862dbb4"
def get_lat_lon(city_name):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={API_KEY_WEATHER}"
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
                weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY_WEATHER}&units=imperial"
                response = requests.get(weather_url)
                api_data = response.json()
                
                weather_data = {
                    "location": name,
                    "temp": round(api_data['main']['temp']),
                    "description": api_data['weather'][0]['description'].title(),
                    "icon": api_data['weather'][0]['icon']
                }

    return render_template('weather.html', weather=weather_data)

class PageSelection(FlaskForm):
    chosen_page = SelectField( 
    choices=[('null','Choose a page')] + ([(route["route"], page) for page, route in pages.items() if page [:4] != "hide"]),
    )

class LogInForm(FlaskForm):
    """
        Flask Form for logging into an account
    """

    username = StringField(
        'Username: ', 
        validators=[validators.DataRequired()]
    )

    password = StringField(
        'Password: ', 
        validators=[validators.DataRequired()]
    )

def attempt_log_in(username, password, form):
    # This is to handle login form submission
    if request.method == 'POST':
        conn = db_connect.get_db_connection()
        # This function checks username/password and returns user data (it should be a dictionary that gets returned) if valid or None if invalid
        user = login_user(conn, username, password)
        conn.close()
        
        if user:
            # Stores user info in the browser session (cookies) to keep them logged in.
            print('3')
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful.')
            return redirect('/dashboard')
        else:
            flash('Login failed. Please try again.')
  
    return render_template('log_in_template.html', form=form)

class SignUpForm(FlaskForm):
    """
        Flask Form for signing up for an account
    """

    username = StringField(
        'Username: ', 
        validators=[validators.DataRequired()]
    )

    password = PasswordField(
        'Password: ', 
        validators=[validators.DataRequired(), validators.Length(min=6)]
    )

    confirmPassword = PasswordField(
        'Confirm Password: ', 
        validators=[validators.DataRequired(), validators.Length(min=6)]
    )


def attempt_sign_up(username, password, confirmPassword, form):
    # password and confirmPassword must match
    if(password != confirmPassword):
        flash('Passwords must match.')
        return render_template('sign_up_template.html', form = form)

    conn = db_connect.get_db_connection()
    # 'signup_user' tries to insert a new row into users table (this is handled by the function).
    # It returns False if the username is already taken.
    success = signup_user(conn, username, password)
    conn.close()

    if success:
        return redirect('/login')
    else:
        flash('Sign up failed. Please try again.')
        return render_template('sign_up_template.html', form = form)


@app.route('/', methods=('GET', 'POST'))
def main():

    form = PageSelection()

    if form.validate_on_submit() and form.chosen_page.data != 'null': 
        return redirect(f'/{form.chosen_page.data}')

    return render_template('main.html', form = form)

# --- These Are The Auth and Dashboard Routes --- (can be change as needed, was mainly used for testing)
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LogInForm()
    if request.method == 'POST' and form.validate_on_submit():
        return attempt_log_in(form.username.data, form.password.data, form)
    return render_template('log_in_template.html', form=form)
    

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if request.method == 'POST' and form.validate_on_submit():
        return attempt_sign_up(form.username.data, form.password.data, form.confirmPassword.data, form)
    return render_template('sign_up_template.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # Check if user is logged in, if not, redirect to login page
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = db_connect.get_db_connection()
    
    # This is to handle adding a widget to the dashboard (the add widget button form submission)
    if request.method == 'POST':
        # The dropdown in HTML sends the name (e.g., "Weather", "Pokemon randomizer")
        widget_to_add = request.form.get('widget_name')
        
        # This helper function handles the SQL to link User -> Widget
        # It also checks for duplicates automatically
        # Feel free to look at or modyfy the function in widget_module/db.py if needed 
        add_widget_to_user(conn, session['user_id'], widget_to_add)
        conn.close()
        return redirect('/dashboard') # Reload page to show new widget (I might be able to change it so it doesn't have to reload the whole page, but this is simpler for now)

    # Load Dashboard Data
    # Fetch the user's active widgets
    my_widgets = get_user_dashboard(conn, session['user_id'])
    
    # Get the list of ALL possible widgets for the "Add" dropdown
    available = get_available_widgets()
    conn.close()
    
    return render_template('dashboard.html', username=session['username'], my_widgets=my_widgets, available_widgets=available)

"""
    Shows the full page view for a single widget.
    'instance_id' is the unique ID of that specific box on the dashboard.
    i.e., if the user clicks on the "details" link for the widget instance. 
"""
@app.route('/details/<int:instance_id>')
def widget_details(instance_id):
    if 'user_id' not in session: return redirect('/login')
    
    conn = db_connect.get_db_connection()
    # Fetch the 'detail' data defined in registry.py
    name, data = get_widget_detail_data(conn, instance_id)
    conn.close()
    
    return render_template('widget_detail.html', name=name, data=data)

"""
    Dynamically builds a settings form based on what the widget needs.
    Example: If widget is "Weather", this form asks for "City".
"""
@app.route('/settings/<int:instance_id>', methods=['GET', 'POST'])
def widget_settings(instance_id):
    if 'user_id' not in session: return redirect('/login')
    
    conn = db_connect.get_db_connection()
    
    # This asks the Registry: "What settings does this widget allow?"
    # Returns the name (e.g. "Weather") and fields (e.g. {'city': 'Salinas'})
    widget_name, config_fields = get_widget_config_fields(conn, instance_id)
    
    if request.method == 'POST':
        # This is to save the form data
        # converts request.form (ImmutableDict) to a regular dict
        form_data = request.form.to_dict()
        # Include any uploaded files so they can be saved to disk and stored
        save_widget_settings(conn, instance_id, form_data, request.files)
        conn.close()
        return redirect('/dashboard')
    
    # Fetch existing values to pre-fill the form
    current_values = get_widget_settings(conn, instance_id)
    conn.close()
    
    return render_template('settings.html', name=widget_name, fields=config_fields, values=current_values)

@app.route('/logout')
def logout():
    session.clear() # Wipes the cookie
    return redirect('/')
#-- This is the end of the Auth and Dashboard Routes ---

for route_info in pages.values():
    if route_info["file"] != "main":
        function_name = route_info["app_function"]
        from_file = importlib.import_module(route_info["file"])
        app_function = getattr(from_file, function_name)
        #[getattr(from_file, imp) for imp in route_info["import"]]
        def view_function(app_function=app_function):
            return render_template("return_to_main_page.html", template=app_function())
        app.add_url_rule(f"/{route_info['route']}", endpoint=function_name, view_func=view_function, methods=['GET', 'POST'])

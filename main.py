import requests, json, sys, os
from pprint import pprint
from flask import Flask, render_template, redirect, request, flash
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, PasswordField, SubmitField, validators
from page_data import pages
import mysql.connector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
bootstrap = Bootstrap5(app)

if database.is_connected():
    print("Successfully connected to MySQL database!")
else:
    print("Failed to connect to MySQL database.")

print(database)

cursor = database.cursor()

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

@app.route('/main', methods=('GET', 'POST'))
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


class SignInForm(FlaskForm):
    username = StringField(
        'Username: ', 
        validators=[validators.DataRequired()]
    )

    password = StringField(
        'Password: ', 
        validators=[validators.DataRequired()]
    )

def attempt_sign_in(username, password):
    sql = "SELECT fname FROM customers WHERE username = %s"
    val = (username)

    if cursor.execute(sql, val):
        sql = "SELECT password FROM customers WHERE username = %s"
        val = (username)
        if password == cursor.execute(sql, val):
            return True
        else:
            flash('Invalid password.', 'info')
            return False
    else:
        flash('Invalid username.', 'info')
        return False

class AccountCreationForm(FlaskForm):
    fname = StringField(
        'First Name: ', 
        validators=[validators.DataRequired()]
    )

    lname = StringField(
        'Last Name: ', 
        validators=[validators.DataRequired()]
    )

    username = StringField(
        'Username: ', 
        validators=[validators.DataRequired()]
    )

    password = PasswordField(
        'Password: ', 
        validators=[validators.DataRequired(), validators.Length(min=6)]
    )

def attempt_account_creation(fname, lname, username, password):
    sql = "SELECT fname FROM customers WHERE username = %s"
    val = (username, )

    if not cursor.execute(sql, val):
        sql = "INSERT INTO customers (fname, lname, username, password) VALUES (%s, %s, %s, %s)"
        val = (fname, lname, username, password)
        cursor.execute(sql, val)
        database.commit()
        return True
    else:
        flash('Username already taken.', 'info')
        return False

@app.route('/', methods=('GET', 'POST'))
def sign_in():
    form = SignInForm()
    if form.validate_on_submit():
        if attempt_sign_in(form.username.data, form.password.data):
            return redirect('/main')
    return render_template('sign_in_template.html', form=form)

@app.route('/create_an_account', methods=('GET', 'POST'))
def create_account():
    form = AccountCreationForm()
    if form.validate_on_submit():
        if attempt_account_creation(form.fname.data, form.lname.data, form.username.data, form.password.data):
            return redirect('/main')
    return render_template('create_account_template.html', form=form)
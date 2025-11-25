import importlib, requests, json, sys, os
from pprint import pprint
from flask import Flask, render_template, redirect, request
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import SelectField
from page_data import pages

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
bootstrap = Bootstrap5(app)

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
    choices=[('null','Choose a page')] + ([(route["route"], page) for page, route in pages.items() if page [:4] != "hide"]),
    )

@app.route('/', methods=('GET', 'POST'))
def main():

    form = PageSelection()

    if form.validate_on_submit() and form.chosen_page.data != 'null': 
        return redirect(f'/{form.chosen_page.data}')

    return render_template('main.html', form = form)

for route_info in pages.values():
    if route_info["file"] != "main":
        function_name = route_info["app_function"]
        from_file = importlib.import_module(route_info["file"])
        app_function = getattr(from_file, function_name)
        #[getattr(from_file, imp) for imp in route_info["import"]]
        def view_function(app_function=app_function):
            return render_template("return_to_main_page.html", template=app_function())
        app.add_url_rule(f"/{route_info['route']}", endpoint=function_name, view_func=view_function, methods=['GET', 'POST'])
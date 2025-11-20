import requests, json, sys, os
from pprint import pprint
from flask import Flask, render_template, redirect
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import SelectField
from page_data import pages

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
bootstrap = Bootstrap5(app)

class PageSelection(FlaskForm):
    chosen_page = SelectField( 
    choices=[('null','Choose a page')] + ([(route, page) for page, route in pages.items()]),
    )

@app.route('/', methods=('GET', 'POST'))
def main():

    form = PageSelection()

    if form.validate_on_submit() and form.chosen_page.data != 'null': 
        return redirect(f'/{form.chosen_page.data}')

    return render_template('main.html', form = form)

@app.route('/test')
def test():
    return render_template("test.html")

@app.route('/example')
def example():
    return render_template("example.html")

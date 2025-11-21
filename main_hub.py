from pprint import pprint
from flask import Flask, render_template, redirect, flash
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, validators

app = Flask(__name__)
app.config['SECRET_KEY'] = 'csumb-otter'
bootstrap = Bootstrap5(app)

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
    print('Attempting Sign-In!')
    print(f'Username: {username}  Password: {password}')

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
    print('Attempting Account Creation!')
    print(f'{fname} {lname}\'s account: ')
    print(f'    Username: {username}  Password: {password}')

@app.route('/', methods=('GET', 'POST'))
def sign_in():
    form = SignInForm()
    if form.validate_on_submit():
        attempt_sign_in(form.username.data, form.password.data)
        return redirect('/content_hub')
    return render_template('sign_in_template.html', form=form)

@app.route('/create_an_account', methods=('GET', 'POST'))
def create_account():
    form = AccountCreationForm()
    if form.validate_on_submit():
        attempt_account_creation(form.fname.data, form.lname.data, form.username.data, form.password.data)
        return redirect('/content_hub')
    return render_template('create_account_template.html', form=form)

@app.route('/content_hub')
def content_hub():
    return render_template('test.html')
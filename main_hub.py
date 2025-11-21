from pprint import pprint
from flask import Flask, render_template, redirect
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'csumb-otter'
bootstrap = Bootstrap5(app)

class SignInForm(FlaskForm):
    username = StringField(
        'Username: ', 
        validators=[DataRequired()]
    )

    password = StringField(
        'Password: ', 
        validators=[DataRequired()]
    )

def attempt_sign_in(username, password):
    print(f'Username: {username}  Password: {password}')

@app.route('/', methods=('GET', 'POST'))
def sign_in():
    form = SignInForm()
    if form.validate_on_submit():
        attempt_sign_in(form.username.data, form.password.data)
        return redirect('/content_hub')
    return render_template('sign_in_template.html', form=form)

@app.route('/create_an_account')
def create_account():
    return render_template('create_account_template.html')


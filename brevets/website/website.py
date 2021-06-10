from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, abort
import requests
import flask

from urllib.parse import urlparse, urljoin
from flask_login import (LoginManager, current_user, login_required, login_user, logout_user, UserMixin, confirm_login, fresh_login_required)
from flask_wtf import FlaskForm as Form
from wtforms import BooleanField, StringField, validators

from passlib.hash import sha256_crypt as pwd_context


def hash_password(password):
    return pwd_context.using(salt="mjsSecretStuff").encrypt(password)


class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=2, max=25, message=u"Must be between 2 and 25 characters."), validators.InputRequired(u"Please enter a username")])
    password = StringField('Password', [validators.Length(min=5, max=25, message=u"Password must be 5-25 characters."), validators.InputRequired(u"Please choose a password")])
    remember = BooleanField('Remember me')


class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=2, max=25, message=u"Username must be 2-25 characters."), validators.InputRequired(u"Please choose a username")])
    password = StringField('Password', [validators.Length(min=5, max=25, message=u"Password must be 5-25 characters."), validators.InputRequired(u"Please choose a password"), validators.EqualTo('repass', message=u'Passwords must be the same!')])
    repass = StringField('Repass')


def is_safe_url(target):
    """
    :source: https://github.com/fengsp/flask-snippets/blob/master/security/redirect_back.py
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username
        self.token = "Unknown"

    def set_token(self, token):
        self.token = token
        return self


oldUSERS = {
    1: User(u"1", u"alex").set_token("token would go here"),
    2: User(u"1", u"bob").set_token("token would go here"),
    3: User(u"1", u"jim").set_token("token would go here"),
}

oldUSER_NAMES = dict((u.username, u) for u in oldUSERS.values())


app = Flask(__name__)
app.secret_key = "and the cats in the cradle and the silver spoon"

app.config.from_object(__name__)

login_manager = LoginManager()

login_manager.session_protection = "strong"

login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."

login_manager.refresh_view = "login"
login_manager.needs_refresh_message = (
    u"To protect your account, please reauthenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return oldUSERS[int(user_id)]


login_manager.init_app(app)


@app.route('/')
@app.route('/index')
def index():
    app.logger.debug("Index")
    return render_template('index.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit() and request.method == "POST" and "username" in request.form:
        username = request.form["username"]
        if username in oldUSER_NAMES:
            remember = request.form.get("remember", "false") == "true"
            if login_user(oldUSER_NAMES[username], remember=remember):
                flash("Logged in!")
                flash("I'll remember you") if remember else None
                next = request.args.get("next")
                if not is_safe_url(next):
                    abort(400)
                return redirect(next or url_for('index'))
            else:
                flash("Sorry, but you could not log in.")
        else:
            flash(u"Invalid username.")
    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit() and request.method == "POST":
        username = request.form["username"]
        hashMe = request.form["password"]
        password = hash_password(hashMe)
        rslt = requests.post(f"http://restapi:5000/register?username={username}&password={password}")
        code = rslt.status_code
        if code == 400:
            flash("Username is alrady taken, pick another one.")
            return redirect(url_for('register'))
        else:
            flash("Registration Successful! Now login to use the calculator!")
            return redirect(url_for('login'))
    return render_template("register.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("index"))


@app.route("/secret")
@login_required
def secret():
    flash(f"Your token is: {current_user.token}")
    return render_template("index.html")


@app.route('/listAll')
def listAll():
    app.logger.debug("List of All")
    format = request.args.get("format", type=str)
    k = request.args.get("k", type=int)
    app.logger.debug(k)
    if format == "json":
        rslt = requests.get(f"http://restapi:5000/listAll/json?top={k}")
    if format == "csv":
        rslt = requests.get(f"http://restapi:5000/listAll/csv?top={k}")
    return rslt.text


@app.route('/listOpenOnly')
def listOpenOnly():
    app.logger.debug("List of Open Only")
    format = request.args.get("format", type=str)
    k = request.args.get("k", type=int)
    if format == "csv":
        rslt = requests.get(f"http://restapi:5000/listOpenOnly/csv?top={k}")
    if format == "json":
        rslt = requests.get(f"http://restapi:5000/listOpenOnly/json?top={k}")
    return rslt.text



@app.route('/listCloseOnly')
def listCloseOnly():
    app.logger.debug("List of Close Only")
    format = request.args.get("format", type=str)
    k = request.args.get("k", type=int)
    if format == "csv":
        rslt = requests.get(f"http://restapi:5000/listCloseOnly/csv?top={k}")
    if format == "json":
        rslt = requests.get(f"http://restapi:5000/listCloseOnly/json?top={k}")
    return rslt.text


@app.route('/listUsers')
def listUsers():
    rslt = requests.get(f"http://restapi:5000/listUsers")
    return rslt.text




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

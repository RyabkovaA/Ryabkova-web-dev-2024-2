from flask import Flask, render_template, session, request, url_for, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user

app = Flask(__name__)
application = app
app.config.from_pyfile('config.py')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth"
login_manager.login_message = "Войдите для просмотра содержимого этой страницы"
login_manager.login_message_category = 'warning'

class User(UserMixin):
    def __init__(self, user_id, login):
        self.id = user_id
        self.login = login

def get_user_list():
    return [{"user_id" : "14", "login" : "root", "password": "admin"},
            {"user_id": "64", "login" : "guest", "password": "qwerty123"},
            {"user_id": "98", "login" : "user", "password": "userpass"}]

@login_manager.user_loader
def load_user(user_id):
    for user_entry in get_user_list():
        if user_id == user_entry["user_id"]:
            return User(user_id, user_entry["login"])
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/info')
def info():
    session['counter'] = session.get('counter', 0) + 1
    return render_template('info.html')

@app.route('/auth', methods=["GET", "POST"])
def auth():
    if request.method == "GET":
        return render_template('auth.html')
    
    login = request.form.get("login", "")
    password = request.form.get("pass", "")
    remember = request.form.get("remember") == "on"

    for user in get_user_list():
        if login == user["login"] and password == user["password"]:
            login_user(User(user["user_id"], user["login"]), remember=remember)
            flash("Авторизация прошла успешно", category='success')
            target_page = request.args.get("next", url_for('index'))
            return redirect(target_page)
        
    flash("Пользователь не найден", category='danger')
    return render_template("auth.html")

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/secret')
def secret():
    if not current_user.is_authenticated:
        flash("Вы не авторизованы", category='warning')
        return redirect(url_for('auth'))

    return render_template('secret.html')
   
# @app.route('/secret')
# @login_required
# def secret():
#     return render_template('secret.html')
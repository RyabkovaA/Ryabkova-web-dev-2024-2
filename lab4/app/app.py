from flask import Flask, render_template, session, request, url_for, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from mysqldb import DBConnector
from mysql.connector.errors import DatabaseError


app = Flask(__name__)
application = app
app.config.from_pyfile('config.py')

db_connector = DBConnector(app)

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

CREATE_USER_FIELDS = ['login', 'password', 'last_name', 'first_name', 'middle_name', 'role_id']
EDIT_USER_FIELDS = ['last_name', 'first_name', 'middle_name', 'role_id']
CHECK_USER_FIELDS = ['login', 'password', 'last_name', 'first_name', 'role_id']

def get_roles():
    query = "SELECT * FROM roles"

    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(query)
        roles = cursor.fetchall()
    return roles

@login_manager.user_loader
def load_user(user_id):
    query = "SELECT id, login FROM users WHERE id=%s"

    with db_connector.connect().cursor(named_tuple=True) as cursor:

        cursor.execute(query, (user_id,))

        user = cursor.fetchone()

    if user:
        return User(user_id, user.login)

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

    query = 'SELECT id, login FROM users WHERE login=%s AND password_hash=SHA2(%s, 256)'
    
    #print(query)

    with db_connector.connect().cursor(named_tuple=True) as cursor:
        
        cursor.execute(query, (login, password))

        print(cursor.statement)

        user = cursor.fetchone()

    if user is not None:
        login_user(User(user.id, user.login), remember=remember)
        flash("Авторизация прошла успешно", category='success')
        target_page = request.args.get("next", url_for('index'))
        return redirect(target_page)
                  
    flash("Введены некорректные учётные данные пользователя", category='danger')
    return render_template("auth.html")

@app.route('/users')
def users():
    query = 'SELECT users.*, roles.name as role_name FROM users LEFT JOIN roles ON users.role_id = roles.id'

    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(query)
        data = cursor.fetchall()
    
    return render_template("users.html", users=data)

def get_form_data(required_fields):
    user = {}
    for field in required_fields:
        user[field] = request.form.get(field) or None

    return user

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    query = ("SELECT * FROM users where id = %s")
    roles = get_roles()
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(query, (user_id, ))
        user = cursor.fetchone() 

    if request.method == "POST":
        user = get_form_data(EDIT_USER_FIELDS)
        print(user)
        user['user_id'] = user_id
        query = ("UPDATE users "
                 "SET last_name=%(last_name)s, first_name=%(first_name)s, "
                 "middle_name=%(middle_name)s, role_id=%(role_id)s "
                 "WHERE id=%(user_id)s ")

        try:
            with db_connector.connect().cursor(named_tuple=True) as cursor:
                cursor.execute(query, user)
                db_connector.connect().commit()
            
            flash("Запись пользователя успешно обновлена", category="success")
            return redirect(url_for('users'))
        except DatabaseError as error:
            flash(f'Ошибка редактирования пользователя! {error}', category="danger")
            db_connector.connect().rollback()    

    return render_template("edit_user.html", user=user, roles=roles)

@app.route('/user/<int:user_id>/delete', methods=["POST"])
@login_required
def delete_user(user_id):
    query = "DELETE FROM users WHERE id=%s"
    try:
        with db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute(query, (user_id, ))
            db_connector.connect().commit() 
        
        flash("Запись пользователя успешно удалена", category="success")
    except DatabaseError as error:
        flash(f'Ошибка удаления пользователя! {error}', category="danger")
        db_connector.connect().rollback()    
    
    return redirect(url_for('users'))

@app.route('/users/<int:user_id>/show', methods=["GET","POST"])
def show_user(user_id):
    query = 'SELECT users.*, roles.name as role_name FROM users LEFT JOIN roles ON users.role_id = roles.id WHERE users.id=%s'
    try:
        with db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute(query, (user_id, ))
            user = cursor.fetchone()
        
    except DatabaseError as error:
        flash(f'Ошибка просмотра пользователя! {error}', category="danger")
        db_connector.connect().rollback()    
    
    return render_template("show_user.html", user=user)


def check_user_data(user):
    errors = {}
    
    for field in CHECK_USER_FIELDS:
        if not user.get(field):
            errors[field] = "Поле не может быть пустым"
    #print(errors)
    if 'login' not in errors:
        if len(user['login']) < 5:
            errors['login'] = "Логин должен содержать не менее 5 символов"
        elif not user['login'].isalnum():
            errors['login'] = "Логин должен состоять только из латинских букв и цифр"
    
    if 'password' not in errors:
        errors['password'] = check_password(user['password'])    

    return errors


def check_password(password):
    if len(password) < 8 or len(password) > 128:
        return "Пароль должен содержать от 8 до 128 символов"
    
    if not any(c.isupper() for c in password) or not any(c.islower() for c in password):
        return "Пароль должен содержать как минимум одну заглавную и одну строчную букву"
    
    if not any(c.isdigit() for c in password):
        return "Пароль должен содержать как минимум одну цифру"
    
    if any(c.isspace() for c in password):
        return "Пароль не должен содержать пробелы"
    
    valid_chars = set("~!?@#$%^&*_-+()[]{}></\\|\"'.,:;")
    for c in password:
        if not (c.isalpha() or c.isdigit() or c in valid_chars): 
            return "Пароль содержит недопустимые символы"

    return None

@app.route('/users/new',  methods=["GET", "POST"])
def create_user():
    user = {}
    roles = get_roles()
    errors = {}

    if request.method == "POST":
        user = get_form_data(CREATE_USER_FIELDS)
        print(user)
        errors = check_user_data(user)
        print(errors)
        if all(value is None for value in errors.values()):
            query = ("INSERT INTO users "
                    "(login, password_hash, last_name, first_name, middle_name, role_id) "
                    "VALUES (%(login)s, SHA2(%(password)s, 256), "
                    "%(last_name)s, %(first_name)s, %(middle_name)s, %(role_id)s)")
            try:
                with db_connector.connect().cursor(named_tuple=True) as cursor:
                    cursor.execute(query, user)
                    db_connector.connect().commit()
                    flash('Пользователь успешно добавлен!', category="success")    
                    return redirect(url_for('users'))
            except DatabaseError as error:
                flash(f'Ошибка создания пользователя! {error}', category="danger")    
                db_connector.connect().rollback()

    return render_template("user_form.html", user=user, roles=roles, errors=errors)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')

@app.route('/password_change',  methods=["GET", "POST"])
@login_required
def password_change():
    errors = {}
    if request.method == "GET":
        return render_template('password_change.html', errors=errors)

    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    repeat_password = request.form.get("repeat_password", "")
    query = 'SELECT password_hash FROM users WHERE login=%s AND password_hash=SHA2(%s, 256)'
    user_password = {}

    try:
        with db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute(query, (current_user.login, old_password))
            user_password = cursor.fetchone()

        if user_password is not None:
            errors['password'] = check_password(new_password)
            if errors['password'] is None:
                if new_password == repeat_password:
                    query = 'UPDATE users SET password_hash=SHA2(%s, 256) WHERE login=%s'
                    with db_connector.connect().cursor(named_tuple=True) as cursor:
                        cursor.execute(query, (new_password, current_user.login))
                        db_connector.connect().commit()   
                        flash("Пароль успешно обновлен", category="success")
                        return redirect(url_for('index'))
                        
                else:
                    errors['dont_match'] = "Пароли не совпадают"
                    flash('Введенные пароли не совпадают!', category="danger")
            else:
                flash('Пароль не соответствует требованиям!', category="danger")
        else:
            errors['wrong_old_password'] = "Неверный пароль"
            flash('Неверно введен старый пароль!', category="danger")
        
    except DatabaseError as error:
        flash(f'Ошибка базы данных! {error}', category="danger")
        db_connector.connect().rollback()     
        
    return render_template('password_change.html', errors=errors)


if __name__ == 'main':
    app.run(debug=True)

# def secret():
#     if not current_user.is_authenticated:
#         flash("Вы не авторизованы", category='warning')
#         return redirect(url_for('auth'))

#     return render_template('secret.html')
   

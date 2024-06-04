from flask import Blueprint, render_template, request, send_file
from app import db_connector
from mysql.connector.errors import DatabaseError
import math
import io
from flask_login import current_user, login_required


logs_bp = Blueprint('logs', __name__, url_prefix='/logs')
PAGE_COUNT = 10

def generate_file(fields, records):
    print(fields)
    print(records)
    result = ','.join(fields) + '\n'
    for record in records:
        line = ','.join([str(getattr(record, field, '') or '') for field in fields]) + '\n'
        result += line
    print(result)
    return io.BytesIO(result.encode())
    

@logs_bp.route('/')
@login_required
def index():
    logs = []
    page_number = request.args.get('page_number', 1, type=int)
    try:
        db_connection = db_connector.connect()
        with db_connection.cursor(named_tuple=True) as cursor:
            if current_user.is_admin():
                query = ("SELECT action_logs.id, users.login, action_logs.path, action_logs.created_at "
                        "FROM action_logs LEFT JOIN users ON action_logs.user_id = users.id "
                        f"LIMIT {PAGE_COUNT} OFFSET {PAGE_COUNT*(page_number - 1)}")
                cursor.execute(query)
                logs = cursor.fetchall()
            else:
                query = ("SELECT action_logs.id, users.login, action_logs.path, action_logs.created_at "
                        f"FROM action_logs LEFT JOIN users ON action_logs.user_id = users.id WHERE users.id = {current_user.id} "
                        f"LIMIT {PAGE_COUNT} OFFSET {PAGE_COUNT*(page_number - 1)}")
                cursor.execute(query)
                logs = cursor.fetchall()


            query = ("SELECT COUNT(*) as count FROM action_logs")
            cursor.execute(query)
            total_count = cursor.fetchone().count
            total_pages = math.ceil(total_count / PAGE_COUNT + 1)
            start_page = max(page_number - 3, 1)
            end_page = min(page_number + 3, total_pages)

            return render_template("action_logs.html", logs=logs, start_page=start_page, end_page=end_page, page_number=page_number)
        
    except DatabaseError as error:
        print(f"Произошла ошибка БД: {error}") 

@logs_bp.route('/users_stat')
@login_required
def users_stat():
    logs = []
    try:
        db_connection = db_connector.connect()
        with db_connection.cursor(named_tuple=True) as cursor:
            query = ("SELECT CONCAT(users.last_name, ' ', users.first_name, ' ', users.middle_name, ' ') AS full_name, COUNT(*) as visit_count, users.login "
                "FROM action_logs LEFT JOIN users ON action_logs.user_id = users.id "
                "GROUP BY users.id ORDER BY visit_count desc")
            cursor.execute(query)
            logs = cursor.fetchall()

            if request.args.get('download'):
                file = generate_file(['login', 'visit_count'], logs)
                return send_file(file, mimetype='text/csv', as_attachment=True, download_name='logs.csv')

            return render_template("users_stat.html", logs=logs)
    except DatabaseError as error:
        print(f"Произошла ошибка БД: {error}") 

@logs_bp.route('/pages_stat')
@login_required
def pages_stat():
    logs = []
    try:
        db_connection = db_connector.connect()
        with db_connection.cursor(named_tuple=True) as cursor:
            query = ("SELECT action_logs.path, COUNT(*) as visit_count "
                "FROM action_logs LEFT JOIN users ON action_logs.user_id = users.id "
                "GROUP BY action_logs.path ORDER BY visit_count desc")
            cursor.execute(query)
            logs = cursor.fetchall()

            if request.args.get('download'):
                file = generate_file(['path', 'visit_count'], logs)
                return send_file(file, mimetype='text/csv', as_attachment=True, download_name='logs.csv')

            return render_template("pages_stat.html", logs=logs)
    except DatabaseError as error:
        print(f"Произошла ошибка БД: {error}") 
    return render_template("logs_base.html")

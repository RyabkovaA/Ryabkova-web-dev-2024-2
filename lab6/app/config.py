import os

SECRET_KEY = 'd0c7ec318ff614fbf08e5b715fb24824d5d980995aee2cc05e8da9d0ea2659f8'


# SQLALCHEMY_DATABASE_URI = 'sqlite:///project.db'
SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://std_2385_lab6:lab6mysql21@std-mysql.ist.mospolytech.ru/std_2385_lab6'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'images')

from flask import Flask
from flaskext.mysql import MySQL
from flask_login import LoginManager

app = Flask(__name__)
mysql = MySQL()

login_manager = LoginManager()
from saiddit import views


app.config['MYSQL_DATABASE_DB'] = 'CSC370'
app.config['MYSQL_DATABASE_HOST'] = 'csc370database.cvbynnnpaqts.us-west-2.rds.amazonaws.com'
mysql.init_app(app)
login_manager.init_app(app)
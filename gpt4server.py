import sys
from flask import Flask, request
from app import app
from data.db import db
import data.user
import data.chat
import controller.user
import controller.chat
import controller.gpt
from waitress import serve
from data.user import Users
from werkzeug.security import generate_password_hash
from pathlib import Path
import os
import uuid
import re
app_data_loc = os.environ.get('APP_DATA_LOC')
web_server_threads = os.environ.get('WEB_SERVER_THREADS') if 'WEB_SERVER_THREADS' in os.environ else 2
if app_data_loc is None:
    app_data_loc = Path.home().joinpath(".cache/gpt4all").as_posix()

print(app_data_loc)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') if 'SECRET_KEY' in os.environ else 'safagwer'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+app_data_loc+'/db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db.init_app(app)
if __name__ == "__main__":   
    if '--migrate' in sys.argv:
        with app.app_context():
            db.create_all()
    elif '--register' in sys.argv:
        with app.app_context():
            usernamer = re.compile('--username=*')
            usernameList = list(filter(usernamer.match, sys.argv))
            passr = re.compile('--pass=*')
            passList = list(filter(passr.match, sys.argv))
            if len(usernameList) == 0 or len(passList) == 0:
                print("username and password needs to be provided")
                exit()
            username = usernameList[0].split("=")[1]
            password = passList[0].split("=")[1]
            hashed_password = generate_password_hash(password, method='sha256')
            if Users.query.filter(Users.name == username).count() > 0:
                print("user exists")
                exit()
            new_user = Users(public_id=str(uuid.uuid4()), name=username, password=hashed_password, admin=False) 
            db.session.add(new_user)  
            db.session.commit()    
    else:
        serve(app, listen='*:5000', threads=web_server_threads)
from app import app
from flask import request, jsonify, make_response
from data.db import db
import jwt
from data.user import Users
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import datetime
from security import token_required, admin_token_required

@app.route('/register', methods=['GET', 'POST'])
@admin_token_required
def signup_user():
    data = request.get_json()
    
    hashed_password = generate_password_hash(data['password'], method='sha256')
 
    new_user = Users(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=False) 
    db.session.add(new_user)  
    db.session.commit()    

    return jsonify({'message': 'registered successfully'})

@app.route('/login', methods=['GET', 'POST'])  
def login_user(): 
 
  auth = request.authorization   

  if not auth or not auth.username or not auth.password:  
     return make_response('could not verify', 401, {'WWW.Authentication': 'Basic realm: "login required"'})    

  user = Users.query.filter_by(name=auth.username).first()   
     
  if check_password_hash(user.password, auth.password):  
     token = jwt.encode({'public_id': user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(hours=30)}, app.config['SECRET_KEY'])  
     return jsonify({'token' : token}) 

  return make_response('could not verify',  401, {'WWW.Authentication': 'Basic realm: "login required"'})

@app.route("/me", methods=['GET'])
@token_required
def get_me(current_user):
   return jsonify(current_user.serialize())
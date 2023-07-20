from flask import request, jsonify
import jwt
from data.user import Users
from app import app
from functools import wraps

def token_required(f):
   @wraps(f)
   def decorator(*args, **kwargs):
    token = None
    if 'x-access-tokens' in request.headers:
        token = request.headers['x-access-tokens']
    if not token:
        return jsonify({'message': 'a valid token is missing'},403)

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], 'HS256')
        current_user = Users.query.filter_by(public_id=data['public_id']).first()
    except Exception as exc:
        print(exc)
        return jsonify({'message': 'token is invalid'},403)

    return f(current_user, *args, **kwargs)
   return decorator

def admin_token_required(f):
   @wraps(f)
   def decorator(*args, **kwargs):
    token = None
    if 'x-access-tokens' in request.headers:
        token = request.headers['x-access-tokens']
    if not token:
        return jsonify({'message': 'a valid token is missing'})

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], 'HS256')
        current_user = Users.query.filter_by(public_id=data['public_id']).first()
        if current_user.admin == False:
            return jsonify({'message': 'admin token is required'},403)
           
    except Exception as exc:
        print(exc)
        return jsonify({'message': 'token is invalid'},403)

    return f(current_user, *args, **kwargs)
   return decorator
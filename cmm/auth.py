from flask import request
from flask_httpauth import HTTPTokenAuth
from models import CmmUsers,db
import sqlalchemy as sa
import jwt
from app import app

auth = HTTPTokenAuth(scheme="Bearer")

@auth.verify_token
def verify_token(token):
    try:
        user = CmmUsers.check_token(token)
        if user!=None:
            data = jwt.decode(token,app.config["SECRET_KEY"],algorithms=['HS256'])
            if 'username' in data:
                return True
    except:
        return False


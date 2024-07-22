from datetime import datetime
from flask import request
from flask_httpauth import HTTPTokenAuth
from models import CmmUsers,db
import jwt
from os import environ

auth = HTTPTokenAuth(scheme="Bearer")

@auth.verify_token
def verify_token(token):
    try:
        user = CmmUsers.check_token(token)
        if user!=None:
            try:
                complete_key = datetime.now().year+datetime.now().month+datetime.now().day
                data = jwt.decode(token,str(environ.get("F2B_TOKEN_KEY"))+str(complete_key),algorithms=['HS256'])
            except Exception as e:
                print(e)
            if 'username' in data:
                return True
    except:
        return False


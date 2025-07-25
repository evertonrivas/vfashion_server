import jwt
import logging
from flask import request
from os import environ, path
from dotenv import load_dotenv
from models.public import SysUsers
from flask_httpauth import HTTPTokenAuth

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

auth = HTTPTokenAuth(scheme="Bearer")

@auth.verify_token
def verify_token(token):
    try:
        # adaptacao para funcionar no pythonanywhere
        if "Authorization" in request.headers and token is None:
            token = request.headers["Authorization"].replace("Bearer ","")

        user = SysUsers.check_token(token)
        if user is not None:
            try:
                data = jwt.decode(token,str(environ.get("F2B_TOKEN_KEY")),algorithms=['HS256'])
                if 'username' in data:
                    return True
            except Exception as e:
                logging.error(e)
        else:
            logging.info("TOKEN:"+str(token))
            # logging.info(request.headers)
            logging.info("Nao encontrou o usuario no BD")
    except Exception as ex:
        logging.error(ex)
        return False


import base64
from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from werkzeug import exceptions
from auth import auth
from config import Config,MailTemplates
from common import _send_email
import mimetypes
import os

ns_upload = Namespace("email",description="Operações para manipular upload de dados")

@ns_upload.route("/")
class EmailApi(Resource):

    @ns_upload.response(HTTPStatus.OK.value,"Realiza envio de arquivo(s) para o servidor")
    @ns_upload.response(HTTPStatus.BAD_REQUEST.value,"Falha ao enviar arquivo(s)!")
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()
            attachs = []

            #verifica se os arquivos existem
            fpath = Config.APP_PATH.value+'assets/tmp/'
            for file in req['attachments']:
                if os.path.exists(fpath+file)==False:
                    return False
                else:
                    with open(fpath+file,"rb") as f:
                        content = base64.b64encode(f.read())
                    attachs.push({
                        "name": file,
                        "type": mimetypes.guess_type(fpath+file),
                        "content": content
                    })
            return _send_email(req['to'],req['subject'],req['content'],MailTemplates.DEFAULT,attachs)
        except exceptions.HTTPException as e:
            return {
                "error_code": e.code,
                "error_details": e.description,
                "error_sql": ''
            }
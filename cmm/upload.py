from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from sqlalchemy import Select, desc, exc, asc
import werkzeug
from auth import auth
from config import Config
import filetype

ns_upload = Namespace("upload",description="Operações para manipular upload de dados")

class UploadList(Resource):
    @ns_upload.response(HTTPStatus.OK.value,"Obtem a listagem de cidades")
    @ns_upload.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_upload.param("file","Arquivo a ser enviado para o servidor","formData")
    def post(self):
        try:
            file = request.files['file']
            ftype = filetype.guess_mime(file.name)
            fpath = Config.APP_PATH.value
            if ftype=='application/pdf':
                fpath += 'assets/pdf/'
            elif ftype=='application/msword' or ftype=='application/vnd.ms-excel' or ftype=='application/vnd.ms-powerpoint':
                fpath += 'assets/docs/'
            elif ftype=='text/plain' or ftype=='text/html' or ftype=='text/richtext':
                fpath += 'assets/docs/'
            elif ftype=='image/png' or ftype=='image/jpeg' or ftype=='image/bmp' or ftype=='image/gif' or ftype=='image/svg+xml' or ftype=='image/tiff':
                fpath += 'assets/images/'
            else:
                fpath += 'assets/unclassified/'
            
            file.save(fpath+'assets/')
            return True
        except werkzeug.exceptions.HTTPException as e:
            print(e)
            return False
        
from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from sqlalchemy import Select, desc, exc, asc,Delete
from werkzeug import exceptions
from auth import auth
from config import Config, CustomerAction
from datetime import datetime
import filetype
from werkzeug.datastructures import ImmutableMultiDict
from models import db,_save_log,CmmLegalEntities,CmmLegalEntityFile
import os

ns_upload = Namespace("upload",description="Operações para manipular upload de dados")

@ns_upload.route("/<int:id>")
class UploadApi(Resource):
    @ns_upload.response(HTTPStatus.OK.value,"Realiza envio de arquivo(s) para o servidor")
    @ns_upload.response(HTTPStatus.BAD_REQUEST.value,"Falha ao enviar arquivo(s)!")
    @ns_upload.param("files[]","Arquivo a ser enviado para o servidor","formData")
    @auth.login_required
    def post(self,id:int):
        try:
            newFileName = ''
            #obtem os arquivos para upload
            files = []
            fileCount = 1
            fpath = Config.APP_PATH.value+'assets/'
            data = ImmutableMultiDict(request.files)
            for file in data.getlist('files[]'):
                parts = file.filename.split(".")
                ext = parts[len(parts)-1]
                if ext=='pdf':
                    ffolder = 'pdf/'
                elif ext=='doc' or ext=='docx' or ext=='xls' or ext=='xlsx' or ext=='ppt' or ext=='pptx':
                    ffolder = 'docs/'
                elif ext=='txt' or ext=='html' or ext=='rtl' or ext=='csv':
                    ffolder = 'docs/'
                elif ext=='png' or ext=='jpeg' or ext=='jpg' or ext=='bmp' or ext=='gif' or ext=='svg' or ext=='tiff':
                    ffolder = 'images/'
                elif ext=='cer' or ext=='p7b' or ext=='pfx' or ext=='p12':
                    ffolder = 'certs/'
                else:
                    ffolder = 'unclassified/'


                #busca as informacoes de cliente para salvar o arquivo
                #tambem atribui um novo nome ao arquivo
                entity = db.session.execute(Select(CmmLegalEntities.taxvat).where(CmmLegalEntities.id==id)).first()
                if entity is not None:
                    #salva o arquivo com outro nome
                    newFileName = entity.taxvat+"_"+str(fileCount)+"_"+datetime.now().strftime("%Y%m%d-%H%M%S")+"."+ext
                    files.append(newFileName)
                    file.save(fpath+ffolder+newFileName)

                    #salva os dados do arquivo no cadastro do cliente
                    file = CmmLegalEntityFile()
                    file.id_legal_entity = id
                    file.content_type = 'Arquivo '+ext if filetype.guess_mime(fpath+ffolder+newFileName) is None else filetype.guess_mime(fpath+ffolder+newFileName)
                    file.folder = ffolder
                    file.name = newFileName
                    db.session.add(file)
                    db.session.commit()
                fileCount += 1

            combinedFiles = ','.join(files)
            _save_log(id,CustomerAction.FA,"Adicionado(s) o(s) arquivo(s) "+combinedFiles)

            return True
        except exceptions.HTTPException as e:
            print("Exception")
            print(e.get_headers())
            return False

    @ns_upload.response(HTTPStatus.OK.value,"Realiza a exclusão de arquivo(s)")
    @ns_upload.response(HTTPStatus.BAD_REQUEST.value,"Falha ao excluir arquivo(s)!")
    @auth.login_required
    def delete(self,id:int):
        try:
            file = db.session.execute(Select(CmmLegalEntityFile.name,
                                             CmmLegalEntityFile.folder,
                                             CmmLegalEntityFile.id_legal_entity,
                                             CmmLegalEntityFile.content_type,
                                             CmmLegalEntityFile.date_created,
                                             CmmLegalEntityFile.date_updated).where(CmmLegalEntityFile.id==id)).first()
            if file is not None:
                if os.path.exists(Config.APP_PATH.value+'assets/'+str(file.folder)+str(file.name)):
                    os.remove(Config.APP_PATH.value+'assets/'+str(file.folder)+str(file.name))
                    db.session.execute(Delete(CmmLegalEntityFile).where(CmmLegalEntityFile.id==id))
                    db.session.commit()
                    _save_log(file.id_legal_entity,CustomerAction.FD,'Removido o arquivo '+file.name)
                return True
        except exceptions.HTTPException as e:
            return False
        

class UploadTmp(Resource):
    @ns_upload.response(HTTPStatus.OK.value,"Realiza envio de arquivo(s) para o servidor na pasta temporaria")
    @ns_upload.response(HTTPStatus.BAD_REQUEST.value,"Falha ao enviar arquivo(s)!")
    @auth.login_required
    def post(self):
        try:
            #obtem os arquivos para upload
            fpath = Config.APP_PATH.value+'assets/tmp/'
            data = ImmutableMultiDict(request.files)
            for file in data.getlist('files[]'):
                file.save(fpath+file.filename)

            return True
        except exceptions.HTTPException as e:
            print(e)
            return False
ns_upload.add_resource(UploadTmp,'/temp')
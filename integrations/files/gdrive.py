import codecs
import io
import json
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth
from googleapiclient.errors import HttpError
import requests
from integrations.files import file
import logging
from os import environ,path,remove

class Gdrive(file.File):
    drive = None
    g_login = None
    link = None
    def __init__(self) -> None:
        super().__init__()
        self.nav.verify = False

    def _get_header(self, type: file.ContentType):
        self.g_login = GoogleAuth(environ.get("F2B_APP_PATH")+'gdrive.yaml')
        
        self.drive = GoogleDrive(self.g_login)
    
    def send(self, fName: str, fFolder: str, fContent: file.FileStorage):
        try:
            self._get_header(file.ContentType.JSON)

            # busca os arquivos existentes pelo nome
            file_list = self.drive.ListFile({"q":"title = '"+fName+"' and trashed=false"}).GetList()
            if len(file_list) > 0:
                for fl in file_list:
                    # apenas atualiza o link e nao faz o upload para nao encher o drive
                    self.link = 'https://drive.google.com/thumbnail?id='+fl['id']+'&sz=w1000'
            else:
                # salva o arquivo na pasta temporaria
                fContent.save(environ.get("F2B_APP_PATH")+'assets/tmp/'+fName)           
                fContent.close()

                file_drive = self.drive.CreateFile({'title': fName})
                file_drive.SetContentFile(environ.get("F2B_APP_PATH")+'assets/tmp/'+fName)
                file_drive.Upload(param={'supportsTeamDrives': True})

                access_token = self.g_login.credentials.access_token
                file_id = file_drive['id']
                url = 'https://www.googleapis.com/drive/v3/files/' + file_id + '/permissions?supportsAllDrives=true'
                headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
                payload = {'type': 'anyone', 'value': 'anyone', 'role': 'reader'}
                res = requests.post(url, data=json.dumps(payload), headers=headers)
                if res.status_code==200:
                    self.link = 'https://drive.google.com/thumbnail?id='+file_drive['id']+'&sz=w1000'

            # access_token = gauth.credentials.access_token # gauth is from drive = GoogleDrive(gauth) Please modify this for your actual script.
            # file_id = file1['id']
            # url = 'https://www.googleapis.com/drive/v3/files/' + file_id + '/permissions?supportsAllDrives=true'
            # headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
            # payload = {'type': 'anyone', 'value': 'anyone', 'role': 'reader'}
            # res = requests.post(url, data=json.dumps(payload), headers=headers)

            # # SHARABLE LINK
            # link = file1['alternateLink']
            
            return True
        except HttpError as e:
            logging.error(e.reason+" => "+e.resp)
        return False
    
    def drop(self,fName:str):
        try:
            file_drive = self.drive.CreateFile({'title': fName})
            file_drive.Delete()
            return True
        except HttpError as e:
            logging.error(e.reason+" => "+e.resp)
        return False
    
    def get(self, id:str, folder:str):
        return self.link
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
import dropbox.files
from dropbox.files import ListFolderResult
from integrations.files import file
from requests import RequestException
import logging
from os import environ

class Dropbox(file.File):
    dbx = dropbox.Dropbox(environ.get("F2B_DROPBOX_TOKEN"))

    def __init__(self) -> None:
        super().__init__()
        self.nav.verify = False
        self.dbx.users_get_current_account()

    def _get_header(self, type: file.ContentType):
        return super()._get_header(type)        

    def send(self, fName: str, fFolder: str, fContent: file.FileStorage):
        try:

            # obtem a lista de pastas
            folders:ListFolderResult = self.dbx.files_list_folder(path="")

            # 
            # caso nao exista cria a pasta
            exists = False
            exists = any(x.name == fFolder for x in folders.entries)
            if exists is False:
                self.dbx.files_create_folder(path="/"+fFolder)

            # envia o arquivo para a pasta na nuvem
            self.dbx.files_upload(f=fContent.read(),path="/"+fFolder+"/"+fName,mode=WriteMode('overwrite'))
            # links = dbx.sharing_list_shared_links(path="/"+fFolder,directory_only=True)
            # https://www.dropbox.com/scl/fi/8fw502pnthhwaetjb6mfk/product_Design-sem-nome-2.png?rlkey=sa75al409vhqwag4sp8glz5cr&st=jc2zep8v&dl=0
            # dbx.files_upload(f.read(), BACKUPPATH, mode=WriteMode('overwrite'))
            self.dbx.close()
            return True
        except AuthError as err:
            logging.error(err.body)
        except ApiError as err:
            # This checks for the specific error where a user doesn't have
            # enough Dropbox space quota to upload this file
            if (err.error.is_path() and
                    err.error.get_path().reason.is_insufficient_space()):
                logging.error("ERROR: Cannot back up; insufficient space.")
            elif err.user_message_text:
                logging.error(err.user_message_text)
            else:
                logging.error(err)
        return False
    
    def drop(self):
        try:
            pass
        except RequestException as e:
            logging.error(e.strerror)
            return False
    
    def get(self,id:str,folder:str):
        try:
            self.dbx.sharing_create_shared_link_with_settings(path="/"+folder+"/"+id)
        except ApiError as e:
            return e.error._value._value.url.replace("dl=0","raw=1")
from config import Config,MailTemplates
import jinja2
import filetype
import pdfkit
import base64
import os
import html.entities
import pathlib
from datetime import date,datetime
from sqlalchemy import Select,func,and_,or_
import requests

def _gen_pdf():
    try:
        #tabela de traducao dos acentos para codigos html
        table = {k: '&{};'.format(v) for k, v in html.entities.codepoint2name.items()}

        tplLoader  = jinja2.FileSystemLoader(searchpath=Config.APP_PATH.value+'assets/layout/')
        tplEnv     = jinja2.Environment(loader=tplLoader)
        layoutFile = "layout.html"
        bodyReport = tplEnv.get_template(layoutFile)

        headerFile   = "header.html"
        headerReport = tplEnv.get_template(headerFile)

        footerFile   = "footer.html"
        footerReport = tplEnv.get_template(footerFile)



        #*****************************************************#
        #               MONTAGEM DO HEADER                    #
        #-----------------------------------------------------#
        header_txt = headerReport.render(
            variavel_existente_no_layout=''
        )
        
        #apaga se o arquivo existir
        if os.path.exists(Config.APP_PATH.value+'assets/layout/header_tmp.html')==True:
            os.remove(Config.APP_PATH.value+'assets/layout/header_tmp.html')

        with open(Config.APP_PATH.value+'assets/layout/header_tmp.html',"w") as file_header:
            file_header.write(header_txt)
            file_header.close()
        #-----------------------------------------------------#
        #            FIM DA MONTAGEM DO HEADER                #
        #*****************************************************#


        #*****************************************************#
        #               MONTAGEM DO FOOTER                    #
        #-----------------------------------------------------#
        footer_txt = footerReport.render(
            variavel_existente_no_layout=''
        )

        #apaga se o arquivo existir
        if os.path.exists(Config.APP_PATH.value+'assets/layout/footer_tmp.html')==True:
            os.remove(Config.APP_PATH.value+'assets/layout/footer_tmp.html')

        with open(Config.APP_PATH.value+'assets/layout/footer_tmp.html',"w") as file_footer:
            file_footer.write(footer_txt)
            file_footer.close()
        #-----------------------------------------------------#
        #            FIM DA MONTAGEM DO FOOTER                #
        #*****************************************************#


        body_txt = bodyReport.render(
                variavel_existente_no_layout=''
            )
        
        fileName = ''
        pdfkit.from_string(body_txt,Config.APP_PATH.value+'assets/pdf/'+fileName+'.pdf',options={
                'encoding': "UTF-8",
                'disable-smart-shrinking':'',
                'header-spacing':10,
                'margin-right': '0mm',
                'margin-left': '0mm',
                'header-html': Config.APP_PATH.value+'assets/layout/header_tmp.html',
                'footer-html': Config.APP_PATH.value+'assets/layout/footer_tmp.html'
            })
        return True
    except Exception as e:
        print(e)
        return False
    
def _send_email(p_to:str,p_subject:str,p_content:str,p_tpl:MailTemplates,p_attach:str=None)->bool:
    return False
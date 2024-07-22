from config import Config,MailTemplates
import jinja2
import pdfkit
import os
import html.entities
from datetime import date,datetime
import requests

def _gen_pdf():
    try:
        #tabela de traducao dos acentos para codigos html
        table = {k: '&{};'.format(v) for k, v in html.entities.codepoint2name.items()}

        tplLoader  = jinja2.FileSystemLoader(searchpath=Config.APP_PATH.value+'assets/layout/')
        tplEnv     = jinja2.Environment(loader=tplLoader)
        layoutFile = "pdf_layout.html"
        bodyReport = tplEnv.get_template(layoutFile)

        headerFile   = "pdf_header.html"
        headerReport = tplEnv.get_template(headerFile)

        footerFile   = "pdf_footer.html"
        footerReport = tplEnv.get_template(footerFile)



        #*****************************************************#
        #               MONTAGEM DO HEADER                    #
        #-----------------------------------------------------#
        header_txt = headerReport.render(
            variavel_existente_no_layout=''
        )
        
        #apaga se o arquivo existir
        if os.path.exists(Config.APP_PATH.value+'assets/layout/pdf_header_tmp.html')==True:
            os.remove(Config.APP_PATH.value+'assets/layout/pdf_header_tmp.html')

        with open(Config.APP_PATH.value+'assets/layout/pdf_header_tmp.html',"w") as file_header:
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
        if os.path.exists(Config.APP_PATH.value+'assets/layout/pdf_footer_tmp.html')==True:
            os.remove(Config.APP_PATH.value+'assets/layout/footer_pdf_tmp.html')

        with open(Config.APP_PATH.value+'assets/layout/pdf_footer_tmp.html',"w") as file_footer:
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

def _send_email(p_to:[],p_cc:[],p_subject:str,p_content:str,p_tpl:MailTemplates,p_attach:[]=None)->bool: # type: ignore
    try:
        tplLoader     = jinja2.FileSystemLoader(searchpath=Config.APP_PATH.value+'assets/layout/')
        tplEnv        = jinja2.Environment(loader=tplLoader)
        layoutFile    = p_tpl.value
        mailTemplate  = tplEnv.get_template(layoutFile)
        mail_template = mailTemplate.render(
            content=p_content,
            url=Config.APP_URL.value +('reset-password/' if p_tpl==MailTemplates.PWD_RECOVERY else None)
        )

        if p_attach is not None:
            json_content= {
                "sender": {
                    "name": Config.EMAIL_SEND_FROM.value,
                    "email": "resultados@neugen.com.br"
                },
                "to": [{
                    "email": one_to.split()
                }for one_to in p_to],
                "cc": [{
                    "email": str(one_cc).split()
                }for one_cc in p_cc],
                "htmlContent": mail_template,
                "subject": p_subject,
                "attachment": [
                    {
                        "content": att['content'],
                        "name": att['filename']
                    }for att in p_attach]
            }
        else:
            json_content= {
                "sender": {
                    "name": Config.EMAIL_SEND_FROM.value,
                    "email": "resultados@neugen.com.br"
                },
                "to": [{
                    "email": one_to.split()
                }for one_to in p_to],
                "cc": [{
                    "email": str(one_cc).split()
                }for one_cc in p_cc],
                "htmlContent": mail_template,
                "subject": p_subject,
            }
        resp = requests.post("https://api.brevo.com/v3/smtp/email",json=json_content,headers={
            'accept':'application/json',
            'content-type': 'application/json',
            'api-key': Config.BREVO_API_KEY.value
        })
        if resp.status_code==200:
            return True
        return False
    except Exception as e:
        print(e)
        return False
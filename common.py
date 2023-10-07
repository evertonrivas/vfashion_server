from config import ConfigEmail,EmailLib,Config,MailTemplates
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
    
def _send_email(p_to:[str],p_subject:str,p_content:str,p_tpl:MailTemplates,p_attach:[str]=None)->bool:

    try:
        tplLoader  = jinja2.FileSystemLoader(searchpath=Config.APP_PATH.value+'assets/layout/')
        tplEnv     = jinja2.Environment(loader=tplLoader)
        layoutFile = MailTemplates.DEFAULT.value
        mailTemplate = tplEnv.get_template(layoutFile)
        mail_template = mailTemplate.render(
            variavel_existente_no_layout=''
        )

        if(ConfigEmail.LIB==EmailLib.GMAIL):
            import smtplib,ssl
            from email import encoders
            from email.mime.base import MIMEBase
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            message = MIMEMultipart("alternative")
            message["Subject"] = p_subject
            message["From"]    = ConfigEmail.GMAIL_USER
            message["To"]      = ",".join(p_to)
            message.attach(MIMEText(mail_template,"html"))

            if len(p_attach)>0:
                for att in p_attach:
                    with open(Config.APP_PATH+'assets/tmp/'+att['name']) as f:
                        part = MIMEBase("application","octet-stream")
                        part.set_payload(f.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={att['name']}"
                )
                message.attach(part)

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com",587,context=context) as server:
                server.login(ConfigEmail.GMAIL_USER,ConfigEmail.GMAIL_PASS)
                server.sendmail(ConfigEmail.GMAIL_USER,p_to,message.as_string())
            return True
        elif(ConfigEmail.LIB==EmailLib.SMTP):
            import smtplib,ssl
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            pass
        elif(ConfigEmail.LIB==EmailLib.SENDGRID):
            #abre o arquivo
            if len(p_attach)>0:
                json_content = {
                    "personalizations":[{
                        "to":[{
                            "email": one_to
                        }for one_to in p_to.split(",")],
                        "subject": p_subject
                    }],
                    "from":{
                        "email":ConfigEmail.SEND_GRID_TO,
                        "name": ConfigEmail.SEND_GRID_TO_NAME
                    },
                    "content":[{
                        "type": "text/html",
                        "value": mail_template
                    }],
                    "attachments":[{
                        "content": att['content'],
                        "type": att['content_type'],
                        "fileName": att['name']
                    }for att in p_attach]
                }
            else:
                json_content = {
                    "personalizations":[{
                        "to":[{
                            "email": one_to
                        }for one_to in p_to.split(",")],
                        "subject": p_subject
                    }],
                    "from":{
                        "email": ConfigEmail.SEND_GRID_TO,
                        "name": ConfigEmail.SEND_GRID_TO_NAME
                    },
                    "content":[{
                        "type": "text/html",
                        "value": mail_template
                    }]
                }
            
            resp = requests.post("https://api.sendgrid.com/v3/mail/send",json=json_content,headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer '+ConfigEmail.SEND_GRID_TOKEN.value
            })
            if resp.ok:
                return True
            return False
    except Exception as e:
        return False
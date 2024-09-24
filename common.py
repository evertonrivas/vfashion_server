from random import seed,randint
from f2bconfig import CustomerAction, MailTemplates, Reports
import jinja2
import pdfkit
import os
import html.entities
import requests
from os import environ
import logging

def _gen_report(fileName:str,_content:object):
    try:
        tplLoader  = jinja2.FileSystemLoader(searchpath=str(environ.get("F2B_APP_PATH"))+'assets/layout/')
        tplEnv     = jinja2.Environment(loader=tplLoader)

        bodyReport = tplEnv.get_template(fileName)

        # arquivo header padrao
        headerFile   = "pdf_f2b_header.html"
        headerReport = tplEnv.get_template(headerFile)

        # arquivo footer padrao
        footerFile   = "pdf_f2b_footer.html"
        footerReport = tplEnv.get_template(footerFile)

        #*****************************************************#
        #               MONTAGEM DO HEADER                    #
        #-----------------------------------------------------#
        #conteudo do header padrao
        header_txt = headerReport.render(title=_content["title"])
        seed(1)
        report_id = randint(0,100000)

        header_temp = str(environ.get("F2B_APP_PATH"))+'assets/layout/pdf_header_tmp_'+str(report_id)+'.html'
        footer_temp = str(environ.get("F2B_APP_PATH"))+'assets/layout/pdf_footer_tmp_'+str(report_id)+'.html'

        with open(header_temp,"w") as file_header:
            file_header.write(header_txt)
            file_header.close()
        #-----------------------------------------------------#
        #            FIM DA MONTAGEM DO HEADER                #
        #*****************************************************#


        #*****************************************************#
        #               MONTAGEM DO FOOTER                    #
        #-----------------------------------------------------#
        footer_txt = footerReport.render(footer=_content["footer"])

        with open(footer_temp,"w") as file_footer:
            file_footer.write(footer_txt)
            file_footer.close()
        #-----------------------------------------------------#
        #            FIM DA MONTAGEM DO FOOTER                #
        #*****************************************************#

        body_txt = bodyReport.render(body=_content["body"],regs=len(_content["body"]))
        
        pdfkit.from_string(body_txt,str(environ.get("F2B_APP_PATH"))+'assets/pdf/'+fileName.replace(".html","")+'.pdf',options={
            'encoding': "UTF-8",
            'disable-smart-shrinking':'',
            'header-spacing':3,
            'margin-right': '5mm',
            'margin-left': '5mm',
            'header-html': header_temp,
            'footer-html': footer_temp
        })
        
        if os.path.exists(header_temp)==True:
            os.remove(header_temp)

        if os.path.exists(footer_temp)==True:
            os.remove(footer_temp)

        return True
    except Exception as e:
        logging.error(e)
        return False

def _send_email(p_to:[],p_cc:[],p_subject:str,p_content:str,p_tpl:MailTemplates,p_attach:[]=None)->bool: # type: ignore
    try:
        tplLoader     = jinja2.FileSystemLoader(searchpath=str(environ.get("F2B_APP_PATH"))+'assets/layout/')
        tplEnv        = jinja2.Environment(loader=tplLoader)
        layoutFile    = p_tpl.value
        mailTemplate  = tplEnv.get_template(layoutFile)
        mail_template = mailTemplate.render(
            content=p_content,
            url=(str(environ.get("F2B_APP_URL"))) +('reset-password/' if p_tpl==MailTemplates.PWD_RECOVERY else "")
        )

        if p_attach is not None:
            json_content= {
                "sender": {
                    "name": str(environ.get("F2B_EMAIL_FROM_NAME")),
                    "email": str(environ.get("F2B_EMAIL_FROM_VALUE"))
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
                    "name": str(environ.get("F2B_EMAIL_FROM_NAME")),
                    "email": str(environ.get("F2B_EMAIL_FROM_VALUE"))
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
            'api-key': str(environ.get("F2B_BREVO_API_KEY"))
        })
        if resp.status_code==200:
            return True
        return False
    except Exception as e:
        logging.error(e)
        return False
    
def _format_action(act:CustomerAction):
    if act==CustomerAction.DATA_REGISTERED.value:
        return "Registro de Dados"
    if act==CustomerAction.DATA_UPDATED.value:
        return "Atualização de Dados"
    if act==CustomerAction.DATA_DELETED.value:
        return "Arquivamento de Dados"
    if act==CustomerAction.MOVE_CRM_FUNNEL.value:
        return "Movimento de Funil/Estágio"
    if act==CustomerAction.CHAT_MESSAGE_SEND.value:
        return "Envio de mensagem"
    if act==CustomerAction.CHAT_MESSAGE_RECEIVED.value:
        return "Recebimento de mensagem"
    if act==CustomerAction.ORDER_CREATED.value:
        return "Pedido criado"
    if act==CustomerAction.ORDER_UPDATED.value:
        return "Pedido atualizado"
    if act==CustomerAction.ORDER_DELETED.value:
        return "Pedido arquivado"
    if act==CustomerAction.SYSTEM_ACCESS.value:
        return "Acesso ao sistema"
    if act==CustomerAction.TASK_CREATED.value:
        return "Tarefa criada"
    if act==CustomerAction.FILE_ATTACHED.value:
        return "Arquivo anexado"
    if act==CustomerAction.FILE_DETTACHED.value:
        return "Arquivo excluído"
    if act==CustomerAction.EMAIL_SENDED.value:
        return "E-mail enviado"
    if act==CustomerAction.EMAIL_REPLIED.value:
        return "E-mail respondido"
    if act==CustomerAction.RETURN_CREATED.value:
        return "Devolução criada"
    if act==CustomerAction.RETURN_UPDATED.value:
        return "Devolução atualizada"
    if act==CustomerAction.FINANCIAL_BLOQUED.value:
        return "Bloqueio financeiro"
    if act==CustomerAction.FINANCIAL_UNBLOQUED.value:
        return "Desbloqueio financeiro"
    if act==CustomerAction.COMMENT_ADDED.value:
        return "Observação"
from enum import Enum

class ShippingCompany(Enum):
    BRASPRESS = 1
    JADLOG    = 2
    JAMEF     = 3
    ECT       = 4

class MailTemplates(Enum):
    DEFAULT      = 'mail_template.html'
    PWD_RECOVERY = 'password_recovery.html'

class CustomerAction(Enum):
    #SA = System Access, TC = Task Created, FA = File Attached, ES = E-mail Sended, ER = E-mail Replied, RC = Return Created, FB = Financial Bloqued/Unbloqued
    DATA_REGISTERED       = 'DR'
    DATA_UPDATED          = 'DU'
    DATA_DELETED          = 'DD'
    MOVE_CRM_FUNNEL       = 'MC'
    CHAT_MESSAGE_SEND     = 'CS'
    CHAT_MESSAGE_RECEIVED = 'CR'
    ORDER_CREATED         = 'OC'
    ORDER_UPDATED         = 'OU'
    ORDER_DELETED         = 'OD'
    SYSTEM_ACCESS         = 'SA'
    TASK_CREATED          = 'TC'
    FILE_ATTACHED         = 'FA'
    FILE_DETTACHED        = 'FD'
    EMAIL_SENDED          = 'ES'
    EMAIL_REPLIED         = 'ER'
    RETURN_CREATED        = 'RC'
    RETURN_UPDATED        = 'RU'
    FINANCIAL_BLOQUED     = 'FB'
    FINANCIAL_UNBLOQUED   = 'FU'
    COMMENT_ADDED         = 'CA'
    
class ContactType(Enum):
    EMAIL = 'E'
    PHONE = 'P'

class OrderStatus(Enum):
    SENDED       = 1 # enviado
    ANALIZING    = 0 # em analise
    PROCESSING   = 2 # processando
    TRANSPORTING = 3 # em transporte
    FINISHED     = 4 # finalizado
    REJECTED     = 5 # rejeitado

class DevolutionStatus(Enum):
    SAVED         = 0 # salvo
    PENDING       = 1 # em andamento
    APPROVED_ALL  = 2 # totalmente aprovada
    APPROVED_PART = 3 # parcialmente aprovada
    REJECTED      = 4 # rejeitada
    FINISHED      = 5 # finalizada

class CrmFunnelType(Enum):
    SALES       = 'S'
    PROSPECTION = 'P'

class LegalEntityType(Enum):
    CUSTOMER       = 'C'
    REPRESENTATIVE = 'R'
    SUPPLIER       = 'S'
    PERSON         = 'P'

class FlimvModel(Enum):
    FLIMVS = "FLIMVS" # seasonal
    FLIMVC = "FLIMVC" # continuous

class ComissionType(Enum):
    FIXED      = 'F'
    COLLECTION = 'C'

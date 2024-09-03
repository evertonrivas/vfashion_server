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

class ProductMassiveAction(Enum):
    CATEGORY = 1
    GRID     = 2
    MODEL    = 3
    PRICE    = 4
    TYPE     = 5
    MEASURE  = 6


class Reports(Enum):
    CUSTOMERS_ACTIVE             = "customers-active"
    CUSTOMERS_INACTIVE           = "customers-inactive"
    CUSTOMERS_HISTORY            = "customers-history"
    CALENDAR_BUDGET              = "calendar-budget"
    CALENDAR_EVENTS              = "calendar-events"
    CRM_CUSTOMERS_PROSPECT       = "crm-customers-prospect"
    CRM_CUSTOMERS_BY_FUNNEL      = "crm-customers-by-funnel"
    DEVOLUTION_BY_CUSTOMER       = "devolution-by-customer"
    DEVOLUTION_BY_MOMENT         = "devolution-by-moment"
    DEVOLUTION_BY_PRODUCT        = "devolution-by-product"
    DEVOLUTION_BY_TYPE           = "devolution-by-type"
    DEVOLUTION_BY_MODEL          = "devolution-by-model"
    DEVOLUTION_BY_CATEGORY       = "devolution-by-category"
    DEVOLUTION_BY_REPRESENTATIVE = "devolution-by-representative"
    DEVOLUTION_BY_STATUS         = "devolution-by-status"
    ORDER_BY_CUSTOMER            = "order-by-customer"
    ORDER_BY_MOMENT              = "order-by-moment"
    ORDER_BY_REPRESENTATIVE      = "order-by-representative"
    ORDER_BY_PRODUCT             = "order-by-product"
    ORDER_BY_TYPE                = "order-by-type"
    ORDER_BY_MODEL               = "order-by-model"
    ORDER_BY_CATEGORY            = "order-by-category"
    ORDER_BY_STATUS              = "order-by-status"
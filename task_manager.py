from config import Config
import importlib

if Config.CONNECT_ERP.value==True:
    ERP = getattr(importlib.import_module(Config.ERP_MODULE.value),Config.ERP_CLASS.value)
    erp = ERP()

    erp.get_representative()
    erp.get_customer()
    erp.get_order()
    erp.create_order()
    erp.get_invoice()
    erp.get_payment_conditions()
    erp.get_products()
    erp.get_bank_slip()
    erp.get_measure_unit()

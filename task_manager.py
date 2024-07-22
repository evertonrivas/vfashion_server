from os import environ
import importlib

if int(environ.get("F2B_CONNECT_ERP"))==1:
    ERP = getattr(importlib.import_module('integrations.'+str(environ.get("F2B_ERP_MODULE"))),str(environ.get("F2B_ERP_CLASS")))
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

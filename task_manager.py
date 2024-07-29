from dotenv import load_dotenv
from os import environ,path
import importlib
from datetime import datetime
from flimv import Flimv

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

# esse eh o job de carga do ERP que eh executado de hora em hora
if datetime.now().strftime("%M")=="08":
    if int(environ.get("F2B_CONNECT_ERP"))==1:
        ERP = getattr(
            importlib.import_module('integrations.'+str(environ.get("F2B_ERP_MODULE"))),
            str(environ.get("F2B_ERP_CLASS"))
        )
        erp = ERP()

        erp.get_representative()
        erp.get_customer()
        erp.get_order()
        erp.get_invoice()
        erp.get_payment_conditions()
        erp.get_products()
        erp.get_bank_slip()
        erp.get_measure_unit()
        erp.create_order()

# esse eh o job que atualiza as informacoes do FLIMV a cada dia sempre as 1h
if datetime.now().strftime("%H%M")=="1040":
    flimv = Flimv()
    flimv.process()
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from os import environ, path, listdir,remove
import importlib
from datetime import datetime
from flimv import Flimv
import csv
from models import CmmLegalEntityImport, CmmProductsImport
from sqlalchemy import Insert, Select, create_engine
import logging

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

# realiza a conexao com o banco de dados
db = create_engine(environ.get("F2B_DB_LIB")+"://"+environ.get("F2B_DB_USER")+":"+environ.get("F2B_DB_PASS")+"@"+environ.get("F2B_DB_HOST")+"/"+environ.get("F2B_DB_NAME"))

# esse eh o job de carga do ERP que eh executado de hora em hora
if datetime.now().strftime("%M")=="00":
    if int(environ.get("F2B_CONNECT_ERP"))==1:
        module = environ.get("F2B_ERP_MODULE")
        class_name = environ.get("F2B_ERP_MODULE").replace("_"," ").title().replace(" ","")
        ERP = getattr(
            importlib.import_module('integrations.'+module),
            class_name
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
# if datetime.now().strftime("%H%M")=="0100":
if datetime.now().strftime("%H%M")=="1040":
    flimv = Flimv()
    flimv.process()



def import_file(fName:str):
    try:
        with open(fName,newline='',encoding="utf-8") as csv_file:
            has_header = csv.Sniffer().has_header(csv_file.read(1024))
            csv_file.seek(0)
            csv_reader = csv.reader(csv_file)
            #pula a linha de cabecalho
            if has_header:
                next(csv_reader)
            with db.connect() as conn:
                if fName.find("import_P_")!=-1:
                    for row in csv_reader:
                        product = {
                            "refCode":row[0],
                            "barCode":row[1],
                            "type":row[2],
                            "model":row[3],
                            "brand":row[4],
                            "name":row[5],
                            "description":row[6],
                            "observation":row[7],
                            "price":float(str(row[8]).replace(",",".")),
                            "measure_unit":row[9],
                            "color":row[10],
                            "size":row[11],
                            "quantity":int(row[12])
                        }
                        conn.execute(Insert(CmmProductsImport),product)
                elif fName.find("import_E_")!=-1:
                    for row in csv_reader:
                        entity = {
                            "id_original":row[0],
                            "taxvat":row[1],
                            "name":row[2],
                            "fantasy_name":row[3],
                            "city":row[4],
                            "postal_code":row[5],
                            "neighborhood":row[6],
                            "address":row[7],
                            "type": "P" if row[8]=='PERSONA' else "C" if row[8]=="CUSTOMER" else "R",
                            "phone_type":row[9],
                            "phone_number":row[10],
                            "is_whatsapp":bool(row[11]),
                            "phone_is_default":bool([row[12]]),
                            "email_type":row[13],
                            "email_address":row[14],
                            "email_is_default":bool(row[15])
                        }
                        conn.execute(Insert(CmmLegalEntityImport),parameters=entity)
                conn.commit()
            #fecha o arquivo
            csv_file.close()

            #realiza a exclusao do arquivo apos importar
            remove(fName)
            process_import()
    except Exception as e:
        logging.error(e)
        print(e)

def process_import():
    try:
        pass
    except Exception as e:
        logging.error(e)

# realiza varredura dos arquivos de importacao e adiciona um em cada thread para execucao
# mesmo por que nao deverao haver muitas importacoes de dados
fpath = environ.get("F2B_APP_PATH")+'assets/import/' 
files = [f for f in listdir(fpath) if path.isfile(fpath+f)]
workers = len(files)+1
for f in files:
    # define uma thread para cada arquivo existente
    with ThreadPoolExecutor(max_workers=workers) as executor:
        ft = executor.submit(import_file,fpath+f)
        print(executor._work_queue)
        print(f)
        #if ft.done:
            # print(executor._work_queue)
        # executor.shutdown(wait=True)
from types import SimpleNamespace
from requests import Session,Response,RequestException
from config import ConfigVirtualAge,Config
from models import CmmMeasureUnit,CmmLegalEntities,B2bOrders, CmmProducts
from sqlalchemy import create_engine,Insert,Select
from integrations.erp import ERP
from time import sleep
import json

class VirtualAge(ERP):
    nav = None
    token_type = ''
    token_access = ''
    conn = None
    def __init__(self) -> None:
        self.nav = Session()
        self.conn = create_engine("mysql+pymysql://"+Config.DB_USER.value+":"+Config.DB_PASS.value+"@"+Config.DB_HOST.value+"/"+Config.DB_NAME.value)
        self.__get_token()

    def __get_object(self,req:Response):
        return json.loads(req.text,object_hook=lambda d: SimpleNamespace(**d))

    def __get_header(self):
        return {
            "Authorization": self.token_type+' '+self.token_access
        }

    def __get_token(self):
        url = ConfigVirtualAge.URL.value+'/api/totvsmoda/authorization/v2/token'
        req = self.nav.post(url,data={
            "grant_type": ConfigVirtualAge.grant_type.value,
            "client_id": ConfigVirtualAge.client_id.value,
            "client_secret": ConfigVirtualAge.client_secret.value,
            "username": ConfigVirtualAge.username.value,
            "password": ConfigVirtualAge.password.value
        },headers={
            "Content-Type":"application/x-www-form-urlencoded"
        })
        if req.status_code==200:
            data = req.json()
            self.token_type   = data['token_type']
            self.token_access = data['access_token']
            return True
        return False
    
    def get_products(self):
        has_next = True
        act_page = 1
        while has_next:
            req = self.nav.post(ConfigVirtualAge.URL.value+'/api/totvsmoda/product/v2/products/search',
                                data={
                                    "filter":{
                                        "change":{
                                            "inProduct":True,
                                            "inPrice":True
                                        }
                                    },
                                    "option":{
                                        "branchInfoCode": ConfigVirtualAge.default_company.value
                                    },
                                    "page": act_page,
                                    "pageSize": 30
                                },
                                headers=self.__get_header())
            if req.status_code==200:
                data = self.__get_object(req)

                for p in data.items:
                    with self.conn.connect() as con:
                        exist = con.execute(Select(CmmProducts).where(CmmProducts.prodCode==p.productCode)).first()
                        if exist!=None:
                            if p.isActive==True:                                
                                result = con.execute(Insert(CmmProducts).values(
                                    prodCode=p.productCode,
                                    barCode=p.productSku,
                                    name=p.productName,
                                    refCode=p.ReferenceCode,
                                    description=p.description,
                                    ncm=p.ncm,
                                    price=0,
                                    price_pdv=0,
                                    measure_unit=p.measuredUnit,
                                    structure='S',
                                    id_category=0,
                                    id_type=0,
                                    id_model=0
                                ))
                                con.commit()
                                
                                imgs = self.__get_product_images(result.inserted_primary_key[0])
                                for img in imgs:
                                    pass


                has_next = data.hasNext
                act_page += 1
                sleep(1)
            else:
                has_next = False

    def __get_product_images(self,id_product:int):
        req = self.nav.post(ConfigVirtualAge.URL.value+'/api/totvsmoda/image/v2/product/search',
                             data={
                                "filter": {
                                    "productCodeList": [
                                    id_product
                                    ]
                                },
                                "page": 1,
                                "pageSize": 1000
                                },headers=self.__get_header())
        if req.status_code==200:
            data = self.__get_object(req)
            if data.items!=None:
                if data.items[0]!=None:
                    if data.items[0].images!=None:
                        return data.items[0].images
        return None

    def get_product_category(self):
        has_next = False
        act_page = 1
        while has_next:
            self.nav.get(ConfigVirtualAge.URL.value+'/')

    def get_representative(self):
        req = self.nav.post(ConfigVirtualAge.URL.value+'/api/api/totvsmoda/person/v2/representatives/search',
                             headers=self.__get_header()
                             )
        if req.status_code==200:
            return self.__get_object(req)
        return False
    
    def get_customer(self,_taxvat:str):
        req = self.nav.post(ConfigVirtualAge.URL.value+'',
                              headers=self.__get_header(),data={
                                
                              })
        if req.status_code==200:
            return self.__get_object(req)
        return False
    
    def create_order(self):
        pass

    def get_order(self):
        pass

    def get_invoice(self,_taxvat:str):
        req = self.nav.post(ConfigVirtualAge.URL.value+'/api/totvsmoda/fiscal/v2/invoices/search',
                      data={
                        "filter": {
                            "branchCodeList": ConfigVirtualAge.active_companies.value,
                            "operationType": "S",
                            "origin": "All",
                            "invoiceStatusList": ["Normal","Issued"],
                            "personCpfCnpjList": [ _taxvat ],
                            "eletronicInvoiceStatusList": ["Authorized","Sent","Generated"]
                        },
                        "page": 1,
                        "pageSize": 50,
                        "expand": "shippingCompany"
                        },
                      headers=self.__get_header())
        if req.status_code==200:
            data = self.__get_object(req)
            
        return None

    def get_measure_unit(self):
        try:
            resp = self.nav.get(ConfigVirtualAge.URL.value+'/api/totvsmoda/product/v2/measurement-unit',
                        headers=self.__get_header())
            if resp.status_code==200:
                data = resp.json()
                with self.conn.connect() as con:
                    for d in data['items']:
                        exist = con.execute(Select(CmmMeasureUnit).where(CmmMeasureUnit.code==d['code'])).first()
                        if exist!=None:
                            con.execute(Insert(CmmMeasureUnit).values(code=d['code'],description=d['description']))
                            con.commit()
                return True
        except RequestException as e:
            print(e.strerror)
            return False
        
    def get_bank_slip(self):

        # resp = Select(B2bOrders.id_customer,CmmLegalEntities.taxvat)\
        # .join(CmmLegalEntities,CmmLegalEntities.id==B2bOrders.id_customer)\
        # .where()

        # resp = requests.post(ConfigVirtualAge.URL.value+'/api/totvsmoda/accounts-receivable/v2/invoices-print/search',
        #                      data={
        #                         "filter":{
        #                             "branchCodeList": ConfigVirtualAge.company_number.value,
        #                             "customerCpfCnpjList": ['']
        #                         }
        #                      },
        #                      headers=self.__get_header())
        # if resp.status_code==200:
        #     data = resp.json()
        pass


    def get_payment_conditions(self):
        pass
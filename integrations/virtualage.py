from requests import RequestException
from config import ConfigVirtualAge
from models import CmmMeasureUnit,CmmLegalEntities,CmmLegalEntityContact,B2bOrders, CmmProducts, CmmProductsCategories
from sqlalchemy import Insert,Select, Update,or_
from integrations.erp import ERP
from time import sleep
import json

class VirtualAge(ERP):
    token_type = ''
    token_access = ''
    def __init__(self) -> None:
        super().__init__()
        self.__get_token()

    def _get_header(self,is_json:bool=True):
        return {
            "Authorization": self.token_type+' '+self.token_access,
            "Content-Type": "application/json" if is_json==True else "text/plain"
        }

    def __get_token(self):
        req = self.nav.post(ConfigVirtualAge.URL.value+'/api/totvsmoda/authorization/v2/token',data={
            "grant_type"   : ConfigVirtualAge.grant_type.value,
            "client_id"    : ConfigVirtualAge.client_id.value,
            "client_secret": ConfigVirtualAge.client_secret.value,
            "username"     : ConfigVirtualAge.username.value,
            "password"     : ConfigVirtualAge.password.value
        },headers={
            "Content-Type":"application/x-www-form-urlencoded"
        })
        if req.status_code==200:
            data = self._as_object(req)
            self.token_type   = data.token_type
            self.token_access = data.access_token
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
                                        "branchInfoCode": ConfigVirtualAge.DEFAULT_COMPANY.value
                                    },
                                    "page": act_page,
                                    "pageSize": 30
                                },
                                headers=self._get_header())
            if req.status_code==200:
                data = self._as_object(req)

                for p in data.items:
                    with self.dbconn.connect() as con:
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
                                
                                self.__save_product_images(result.inserted_primary_key[0])
                has_next = data.hasNext
                act_page += 1
                sleep(1)
            else:
                has_next = False

    def __save_product_images(self,id_product:int):
        req = self.nav.post(ConfigVirtualAge.URL.value+'/api/totvsmoda/image/v2/product/search',
                             data={
                                "filter": {
                                    "productCodeList": [
                                    id_product
                                    ]
                                },
                                "page": 1,
                                "pageSize": 1000
                                },headers=self._get_header())
        if req.status_code==200:
            data = self._as_object(req)
            if data.items!=None:
                if data.items[0]!=None:
                    if data.items[0].images!=None:
                        return data.items[0].images
        return None

    def get_product_category(self):
        has_next = True
        act_page = 1
        #faz um looping infinito por causa da paginacao de resultados
        while has_next:
            req = self.nav.get(ConfigVirtualAge.URL.value+'/api/totvsmoda/product/v2/category',
                               data={
                                    "page": act_page,
                                    "pageSize": 100
                                },
                                headers=self._get_header()
                                )
            #verifica se houve sucesso na busca
            if req.status_code==200:
                #converte o resultado em objeto
                data = self._as_object(req)
                #varre os itens do resultado
                for it in data.items:
                    #conecta o bd
                    with self.dbconn.connect() as con:
                        #verifica se o registro ja existe
                        exist = con.execute(Select(CmmProductsCategories).where(CmmProductsCategories.orign_id==it.code)).first()
                        if exist!=None:
                            #so irah salvar o que for categoria ou subcategoria
                            if it.categoryType==1 or it.categoryType==2:
                                con.execute(Insert(CmmProductsCategories).values(name=it.name,id_parent=it.parentCategoryCode,origin_id=it.code))
                                con.commit()
            else:
                #ao gerar falha na busca interrompe o looping
                has_next = False
            has_next = data.hasNext
            act_page += 1
            #da um tempo pra nao sobrecarregar a API
            sleep(1)
        return True

    def get_representative(self):
        try:
            has_next = True
            act_page = 1

            while has_next:
                #se nao preencheu a lista de REPS buscarah tudo o que existe na API
                if ConfigVirtualAge.ACTIVE_REPS.value!="":
                    filter = {
                        "filter":{
                            "representativeCodeList": ConfigVirtualAge.ACTIVE_REPS.value
                        },
                        "expand": "addresses,emails,phones,customers",
                        "page" : act_page
                    }
                else:
                    filter = {
                        "expand": "addresses,emails,phones",
                        "page" : act_page
                    }

                req = self.nav.post(ConfigVirtualAge.URL.value+'/api/totvsmoda/person/v2/representatives/search',
                                    data=json.dumps(filter),
                                    headers=self._get_header()
                                    )
                if req.status_code==200:
                    #transforma a resposta em objeto
                    data = self._as_object(req)
                    #varre os itens
                    for it in data.items:
                        #connecta o BD
                        with self.dbconn.connect() as conn:
                            #verifica se ja existe cadastro importado ou se ja tem cadastro do CNPJ
                            exist = conn.execute(Select(CmmLegalEntities).where(or_(CmmLegalEntities.origin_id==it.code,CmmLegalEntities.taxvat==it.cpfCnpj))).first()
                            #se nao existir ira cadastrar
                            if exist==None:
                                res = conn.execute(Insert(CmmLegalEntities).values(
                                    origin_id = it.code,
                                    name = it.name,
                                    taxvat = it.cpfCnpj,
                                    state_region = it.addresses[0].stateAbbreviation,
                                    city = it.addresses[0].cityName,
                                    postal_code = it.addresses[0].cep,
                                    neighborhood = it.addresses[0].neighborhood,
                                    type="R"
                                ))
                                conn.commit()

                                #importa os emails do cadastro
                                for em in it.emails:
                                    self.__save_contact(conn,em,"E",res.inserted_primary_key[0])

                                #importa os telefones do cadastro
                                for ph in it.phones:
                                    self.__save_contact(conn,ph,"P",res.inserted_primary_key[0])

                                if it.customers!=None:
                                    for cs in it.customers:
                                        self.get_customer(False,cs.cpfCnpj)
                            else:
                                #aqui irah atualizar as informacoes de cadastro
                                conn.execute(Update(CmmLegalEntities).values(
                                    origin_id    = it.code if it.code!=exist.origin_id else exist.origin_id,
                                    name         = it.name if it.name!=exist.name else exist.name,
                                    taxvat       = it.cpfCnpj if it.cpfCnpj!=exist.taxvat else exist.taxvat,
                                    state_region = it.addresses[0].stateAbbreviation if it.addresses[0].stateAbbreviation!=exist.state_region else exist.state_region,
                                    city         = it.addresses[0].cityName if it.addresses[0].cityName!=exist.city else exist.city,
                                    postal_code  = it.addresses[0].cep if it.addresses[0].cep!=exist.postal_code else exist.postal_code,
                                    neighborhood = it.addresses[0].neighborhood if it.addresses[0].neighborhood!=exist.neighborhood else exist.neighborhood
                                ).where(CmmLegalEntities.id==exist.id))
                                conn.commit()
                                for em in it.emails:
                                    exist = conn.execute(Select(CmmLegalEntityContact).where(CmmLegalEntityContact.value==em.email)).first()
                                    if exist==None:
                                        self.__save_contact(conn,em,"E",exist.id)
                                
                                for ph in it.phones:
                                    number = str(ph.number).replace(" ","").replace("(","").replace(")","").replace("-","")
                                    exist = conn.execute(Select(CmmLegalEntityContact).where(CmmLegalEntityContact.value==number))
                                    if exist==None:
                                        self.__save_contact(conn,ph,"P",exist.id)
                                
                                if it.customers!=None:
                                    for cs in it.customers:
                                        self.get_customer(False,cs.cpfCnpj)
                else:
                    # print(req.status_code)
                    # print(req.text)
                    has_next = False
                has_next = bool(data.hasNext)
                act_page += 1
        except RequestException as e:
            print(e)
            return False
    
    def get_customer(self,all:bool=True,taxvat:str=""):
        try:
            act_page = 1
            has_next = True
            while has_next:

                if all==False:
                    filter = {
                        "filter":{
                            "isCustomer": True,
                            "isSupplier": False,
                            "isRepresentative": False,
                            "isPurchasingGuide": False,
                            "isShippingCompany": False,
                            "cnpjList": [taxvat]
                        },
                        "expand": "phones,emails,addresses",
                        "page": act_page,
                        "pageSize": 500
                    }
                else:
                    filter = {
                        "filter":{
                            "isCustomer": True,
                            "isSupplier": False,
                            "isRepresentative": False,
                            "isPurchasingGuide": False,
                            "isShippingCompany": False
                        },
                        "expand": "phones,emails,addresses",
                        "page": act_page,
                        "pageSize": 500
                    }

                req = self.nav.post(ConfigVirtualAge.URL.value+'/api/totvsmoda/person/v2/legal-entities/search',headers=self._get_header(),data=json.dumps(filter))
                if req.status_code==200:
                    data = self._as_object(req)
                    for it in data.items:
                        with self.dbconn.connect() as conn:
                            clear_cnpj = str(it.cnpj).replace(" ","").replace("/","").replace("-","").replace(".","")
                            exist = conn.execute(Select(CmmLegalEntities).where(CmmLegalEntities.taxvat==clear_cnpj)).first()
                            if exist==None:
                                resp = conn.execute(Insert(CmmLegalEntities).values(
                                    origin_id = it.code,
                                    name = it.name,
                                    fantasy_name = it.fantasyName,
                                    taxvat = clear_cnpj,
                                    state_region = it.addresses[0].stateAbbreviation,
                                    city = it.addresses[0].cityName,
                                    postal_code = it.addresses[0].cep,
                                    neighborhood = it.addresses[0].neighborhood,
                                    type="C"
                                ))
                                conn.commit()

                                #importa os emails do cadastro
                                for em in it.emails:
                                    self.__save_contact(conn,em,"E",resp.inserted_primary_key[0])

                                #importa os telefones do cadastro
                                for ph in it.phones:
                                    self.__save_contact(conn,ph,"P",resp.inserted_primary_key[0])
                            else:
                                resp = conn.execute(Update(CmmLegalEntities).values(
                                    origin_id = it.code,
                                    name = it.name,
                                    fantasy_name = it.fantasyName,
                                    state_region = it.addresses[0].stateAbbreviation,
                                    city = it.addresses[0].cityName,
                                    postal_code = it.addresses[0].cep,
                                    neighborhood = it.addresses[0].neighborhood,
                                    type="C"
                                ).where(CmmLegalEntities.taxvat==clear_cnpj))
                                conn.commit()

                                for em in it.emails:
                                        exist = conn.execute(Select(CmmLegalEntityContact).where(CmmLegalEntityContact.value==em.email)).first()
                                        if exist==None:
                                            self.__save_contact(conn,em,"E",exist.id)
                                    
                                for ph in it.phones:
                                    number = str(ph.number).replace(" ","").replace("(","").replace(")","").replace("-","")
                                    exist = conn.execute(Select(CmmLegalEntityContact).where(CmmLegalEntityContact.value==number))
                                    if exist==None:
                                        self.__save_contact(conn,ph,"P",exist.id)

                else:
                    print(req.status_code)
                    print(req.text)
                    has_next = False
                
                has_next = data.hasNext
                act_page += 1
        except RequestException as e:
            print(e)
            return False
    
    def __save_contact(self,conn,obj,contact_type,id = None):
        conn.execute(Insert(CmmLegalEntityContact).values(
                id_legal_entity=id,
                contact_type = contact_type,
                is_whatsapp = False,
                value = str(obj.email).replace(" ","") if contact_type=="E" else str(obj.number).replace(" ","").replace("(","").replace(")","").replace("-",""),
                is_default = bool(obj.isDefault),
                name = obj.typeName
            ))
        conn.commit()

    def create_order(self):
        pass

    def get_order(self):
        pass

    def get_invoice(self,_taxvat:str):
        req = self.nav.post(ConfigVirtualAge.URL.value+'/api/totvsmoda/fiscal/v2/invoices/search',
                      data={
                        "filter": {
                            "branchCodeList": ConfigVirtualAge.ACTIVE_COMPANIES.value,
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
                      headers=self._get_header())
        if req.status_code==200:
            data = self._as_object(req)
            
        return None

    def get_measure_unit(self):
        try:
            has_next = True
            act_page = 1
            while has_next:
                req = self.nav.get(ConfigVirtualAge.URL.value+'/api/totvsmoda/product/v2/measurement-unit',
                            headers=self._get_header())
                if req.status_code==200:
                    data = self._as_object(req)
                    with self.dbconn.connect() as con:
                        for d in data.items:
                            exist = con.execute(Select(CmmMeasureUnit).where(CmmMeasureUnit.code==d.code)).first()
                            if exist!=None:
                                con.execute(Insert(CmmMeasureUnit).values(code=d.code,description=d.description))
                                con.commit()
                else:
                    has_next = False
                has_next = data.hasNext
                act_page += 1
            return True
        except RequestException as e:
            #print(e.strerror)
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
        #                      headers=self._get_header())
        # if resp.status_code==200:
        #     data = resp.json()
        pass

    def get_payment_conditions(self):
        pass
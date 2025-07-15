import json
from time import sleep
from os import environ
# from models import _show_query
from integrations.erp import erp
from requests import RequestException
from models.tenant import CmmStateRegions, CmmCategories
from models.tenant import CmmProductsCategories,CmmCities
from models.tenant import CmmMeasureUnit,CmmLegalEntities
from sqlalchemy import Insert,Select, Update, and_,or_,exc
from models.tenant import CmmLegalEntityContact,CmmProducts

class VirtualAge(erp.ERP):
    token_type = ''
    token_access = ''
    def __init__(self, _schema:str) -> None:
        super().__init__(schema=_schema)
        self.__get_token()

    def _get_header(self,is_json:bool=True):
        return {
            "Authorization": self.token_type+' '+self.token_access,
            "Content-Type": "application/json" if is_json else "text/plain"
        }

    def __get_token(self):
        req = self.nav.post(str(environ.get("F2B_VIRTUALAGE_URL"))+'/api/totvsmoda/authorization/v2/token',data={
            "grant_type"   : environ.get("F2B_VIRTUALAGE_GRANT_TYPE"),
            "client_id"    : environ.get("F2B_VIRTUALAGE_CLIENT_ID"),
            "client_secret": environ.get("F2B_VIRTUALAGE_CLIENT_SECRET"),
            "username"     : environ.get("F2B_VIRTUALAGE_USERNAME"),
            "password"     : environ.get("F2B_VIRTUALAGE_PASSWORD")
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
            req = self.nav.post(str(environ.get("F2B_VIRTUALAGE_URL"))+'/api/totvsmoda/product/v2/products/search',
                                data={
                                    "filter":{
                                        "change":{
                                            "inProduct":True,
                                            "inPrice":True
                                        }
                                    },
                                    "option":{
                                        "branchInfoCode": environ.get("F2B_VIRTUALAGE_DEFAULT_COMPANY")
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
                        if exist is not None:
                            if not p.isActive:                                
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

                                inserted_id = result.inserted_primary_key[0] if hasattr(result, "inserted_primary_key") and result.inserted_primary_key else None
                                
                                self.__save_product_images(int(str(inserted_id)))
                has_next = data.hasNext
                act_page += 1
                sleep(1)
            else:
                has_next = False

    def __save_product_images(self,id_product:int):
        req = self.nav.post(str(environ.get("F2B_VIRTUALAGE_URL"))+'/api/totvsmoda/image/v2/product/search',
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
            if data.items is not None:
                if data.items[0] is not None:
                    if data.items[0].images is not None:
                        return data.items[0].images
        return None

    def get_product_category(self):
        has_next = True
        act_page = 1
        #faz um looping infinito por causa da paginacao de resultados
        while has_next:
            req = self.nav.get(str(environ.get("F2B_VIRTUALAGE_URL"))+'/api/totvsmoda/product/v2/category',
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
                        exist = con.execute(Select(CmmProductsCategories)\
                                .join(CmmCategories,CmmCategories.id==CmmProductsCategories.id_category)\
                                .where(CmmCategories.origin_id==it.code)).first()
                        if exist is not None:
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
                if environ.get("F2B_VIRTUALAGE_ACTIVE_REPS")!="":
                    filter = {
                        "filter":{
                            "representativeCodeList": environ.get("F2B_VIRTUALAGE_ACTIVE_REPS")
                        },
                        "expand": "addresses,emails,phones,customers",
                        "page" : act_page
                    }
                else:
                    filter = {
                        "expand": "addresses,emails,phones",
                        "page" : act_page
                    }

                req = self.nav.post(str(environ.get("F2B_VIRTUALAGE_URL"))+'/api/totvsmoda/person/v2/representatives/search',
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
                            if exist is None:
                                res = conn.execute(Insert(CmmLegalEntities).values(
                                    origin_id    = it.code,
                                    name         = it.name,
                                    fantasy_name = it.name,
                                    taxvat       = it.cpfCnpj,
                                    id_city      = self._get_id_city(it.addresses[0].ibgeCityCode,it.addresses[0].stateAbbreviation),
                                    postal_code  = it.addresses[0].cep,
                                    neighborhood = it.addresses[0].neighborhood,
                                    address      = it.addresses[0].address +','+str(it.addresses[0].addressNumber),
                                    type         = "R"
                                ))
                                conn.commit()

                                #importa os emails do cadastro
                                for em in it.emails:
                                    inserted_id = res.inserted_primary_key[0] if hasattr(res, "inserted_primary_key") and res.inserted_primary_key else None
                                    self.__save_contact(conn,em,"E",inserted_id)

                                #importa os telefones do cadastro
                                for ph in it.phones:
                                    inserted_id = res.inserted_primary_key[0] if hasattr(res, "inserted_primary_key") and res.inserted_primary_key else None
                                    self.__save_contact(conn,ph,"P",inserted_id)

                                #importa os clientes do representante
                                if it.customers is not None:
                                    for cs in it.customers:
                                        self.get_customer(False,cs.cpfCnpj)
                            else:
                                #aqui irah atualizar as informacoes de cadastro
                                conn.execute(Update(CmmLegalEntities).values(
                                    origin_id    = it.code if it.code!=exist.origin_id else exist.origin_id,
                                    name         = it.name if it.name!=exist.name else exist.name,
                                    fantasy_name = it.name if it.name!=exist.fantasy_name else exist.fantasy_name,
                                    taxvat       = it.cpfCnpj if it.cpfCnpj!=exist.taxvat else exist.taxvat,
                                    id_city      = self._get_id_city(it.addresses[0].ibgeCityCode,it.addresses[0].stateAbbreviation) if self._get_id_city(it.addresses[0].ibgeCityCode,it.addresses[0].stateAbbreviation)!=exist.id_city else exist.id_city,
                                    postal_code  = it.addresses[0].cep if it.addresses[0].cep!=exist.postal_code else exist.postal_code,
                                    neighborhood = it.addresses[0].neighborhood if it.addresses[0].neighborhood!=exist.neighborhood else exist.neighborhood,
                                    address      = it.addresses[0].address+','+str(it.addresses[0].addressNumber) if it.addresses[0].address else exist.address
                                ).where(CmmLegalEntities.id==exist.id))
                                conn.commit()
                                for em in it.emails:
                                    exist = conn.execute(Select(CmmLegalEntityContact).where(CmmLegalEntityContact.value==em.email)).first()
                                    if exist is not None:
                                        self.__save_contact(conn,em,"E",(0 if exist is not None else exist.id))
                                
                                for ph in it.phones:
                                    number = str(ph.number).replace(" ","").replace("(","").replace(")","").replace("-","")
                                    exist = conn.execute(Select(CmmLegalEntityContact).where(CmmLegalEntityContact.value==number))
                                    if exist is not None:
                                        self.__save_contact(conn,ph,"P",(0 if exist is not None else exist.id))
                                
                                #importa os clientes do representante
                                if it.customers is not None:
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
        
    def _get_id_city(self,p_ibge_code:str,p_state:str):
        try:
            with self.dbconn.connect() as con:
                stmt = Select(CmmCities)\
                    .join(CmmStateRegions,CmmStateRegions.id==CmmCities.id_state_region)\
                    .where(
                        and_(
                            CmmCities.brazil_ibge_code.like('%{}'.format(p_ibge_code)),
                            CmmStateRegions.acronym==p_state
                        )
                    )
                ct = con.execute(stmt).one_or_none()
                return ct.id if ct is not None else 0
        except exc.SQLAlchemyError as e:
            print(e)
            return 0
    
    def get_customer(self,all:bool=True,taxvat:str=""):
        try:
            act_page = 1
            has_next = True
            while has_next:

                if not all:
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

                req = self.nav.post(str(environ.get("F2B_VIRTUALAGE_URL"))+'/api/totvsmoda/person/v2/legal-entities/search',headers=self._get_header(),data=json.dumps(filter))
                if req.status_code==200:
                    data = self._as_object(req)
                    for it in data.items:
                        with self.dbconn.connect() as conn:
                            clear_cnpj = str(it.cnpj).replace(" ","").replace("/","").replace("-","").replace(".","")
                            exist = conn.execute(Select(CmmLegalEntities).where(CmmLegalEntities.taxvat==clear_cnpj)).first()
                            if exist is not None:
                                resp = conn.execute(Insert(CmmLegalEntities).values(
                                    origin_id = it.code,
                                    name = it.name,
                                    fantasy_name = it.name,
                                    taxvat = clear_cnpj,
                                    id_city = self._get_id_city(it.addresses[0].ibgeCityCode,it.addresses[0].stateAbbreviation),
                                    postal_code = it.addresses[0].cep,
                                    neighborhood = it.addresses[0].neighborhood,
                                    address      = it.addresses[0].address +','+str(it.addresses[0].addressNumber),
                                    type="C"
                                ))
                                conn.commit()

                                #importa os emails do cadastro
                                for em in it.emails:
                                    inserted_id = resp.inserted_primary_key[0] if hasattr(resp, "inserted_primary_key") and resp.inserted_primary_key else None
                                    self.__save_contact(conn,em,"E",inserted_id)

                                #importa os telefones do cadastro
                                for ph in it.phones:
                                    inserted_id = resp.inserted_primary_key[0] if hasattr(resp, "inserted_primary_key") and resp.inserted_primary_key else None
                                    self.__save_contact(conn,ph,"P",inserted_id)
                            else:
                                resp = conn.execute(Update(CmmLegalEntities).values(
                                    origin_id = it.code,
                                    name = it.name,
                                    fantasy_name = it.name,
                                    id_city = self._get_id_city(it.addresses[0].ibgeCityCode,it.addresses[0].stateAbbreviation),
                                    postal_code = it.addresses[0].cep,
                                    neighborhood = it.addresses[0].neighborhood,
                                    address      = it.addresses[0].address +','+str(it.addresses[0].addressNumber),
                                    type="C"
                                ).where(CmmLegalEntities.taxvat==clear_cnpj))
                                conn.commit()

                                for em in it.emails:
                                        exist = conn.execute(Select(CmmLegalEntityContact).where(CmmLegalEntityContact.value==em.email)).first()
                                        if exist is not None:
                                            self.__save_contact(conn,em,"E",exist.id)
                                    
                                for ph in it.phones:
                                    number = str(ph.number).replace(" ","").replace("(","").replace(")","").replace("-","")
                                    exist = conn.execute(Select(CmmLegalEntityContact).where(CmmLegalEntityContact.value==number)).first()
                                    if exist is not None:
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
        req = self.nav.post(str(environ.get("F2B_VIRTUALAGE_URL"))+'/api/totvsmoda/fiscal/v2/invoices/search',
                      data={
                        "filter": {
                            "branchCodeList": environ.get("F2B_VIRTUALAGE_ACTIVE_COMPANIES"),
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
            return data
            
        return None

    def get_measure_unit(self):
        try:
            has_next = True
            act_page = 1
            while has_next:
                req = self.nav.get(str(environ.get("F2B_VIRTUALAGE_URL"))+'/api/totvsmoda/product/v2/measurement-unit',
                            headers=self._get_header())
                if req.status_code==200:
                    data = self._as_object(req)
                    with self.dbconn.connect() as con:
                        for d in data.items:
                            exist = con.execute(Select(CmmMeasureUnit).where(CmmMeasureUnit.code==d.code)).first()
                            if exist is not None:
                                con.execute(Insert(CmmMeasureUnit).values(code=d.code,description=d.description))
                                con.commit()
                else:
                    has_next = False
                has_next = data.hasNext
                act_page += 1
            return True
        except RequestException:
            #print(e.strerror)
            return False
        
    def get_bank_slip(self):

        # resp = Select(B2bOrders.id_customer,CmmLegalEntities.taxvat)\
        # .join(CmmLegalEntities,CmmLegalEntities.id==B2bOrders.id_customer)\
        # .where()

        # resp = requests.post(environ.get("F2B_VIRTUALAGE_URL")+'/api/totvsmoda/accounts-receivable/v2/invoices-print/search',
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
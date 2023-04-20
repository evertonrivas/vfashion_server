from integrations.erp import ERP
from requests import Response,Session,RequestException

class Webpic(ERP):
    def __get_object(self, req: Response):
        return super().__get_object(req)
    
    def get_bank_slip(self):
        return super().get_bank_slip()
    
    def get_customer(self, taxvat: str):
        return super().get_customer(taxvat)
    
    def get_invoice(self):
        return super().get_invoice()
    
    def get_measure_unit(self):
        return super().get_measure_unit()
    
    def get_order(self):
        return super().get_order()
    
    def get_products(self):
        return super().get_products()
    
    def get_representative(self):
        return super().get_representative()
    
    def get_payment_conditions(self):
        return super().get_payment_conditions()
    
    def create_order(self):
        return super().create_order()
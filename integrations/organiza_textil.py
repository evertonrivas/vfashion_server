from integrations.erp import ERP
from requests import RequestException

class OrganizaTextil(ERP):
    def _get_header(self):
        return super()._get_header()
    
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
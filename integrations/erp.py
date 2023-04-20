from abc import abstractmethod,ABC
from requests import Response


class ERP(ABC):
    @abstractmethod
    def __get_header(self):
        pass

    @abstractmethod
    def __get_object(self,req:Response):
        pass

    @abstractmethod
    def get_representative(self):
        pass

    @abstractmethod
    def get_customer(self,taxvat:str):
        pass

    @abstractmethod
    def get_order(self):
        pass

    @abstractmethod
    def create_order(self):
        pass

    @abstractmethod
    def get_invoice(self):
        pass

    @abstractmethod
    def get_measure_unit(self):
        pass

    @abstractmethod
    def get_bank_slip(self):
        pass

    @abstractmethod
    def get_products(self):
        pass

    @abstractmethod
    def get_payment_conditions(self):
        pass
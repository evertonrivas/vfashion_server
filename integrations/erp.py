from abc import abstractmethod,ABC


class ERP(ABC):
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
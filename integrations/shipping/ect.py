from datetime import datetime
from integrations.shipping import shipping
from requests import RequestException
import logging

class Ect(shipping.Shipping):
    pass
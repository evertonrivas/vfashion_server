from config import ShippingCompany
import requests
import urllib3
from datetime import datetime
from os import environ

class Shipping():
    nav = None
    shp = None
    def __init__(self) -> None:
        #remove o warning de excessao da verificacao do certificado SSL
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.nav = requests.Session()

    def tracking(self,_shp:ShippingCompany,options:object):
        if _shp==ShippingCompany.BRASPRESS:
            return self.__braspress_tracking(_taxvat=options.taxvat,_invoice=options.invoice)
        if _shp==ShippingCompany.JADLOG:
            return self.__jadlog_tracking(_nf=options.invoice,_nf_serie=options.invoice_serie,_cnpj=options.taxvat)
        if _shp==ShippingCompany.JAMEF:
            return self.__jamef_tracking(_cnpj=options.taxvat,_nf=options.invoice,_serie_nf=options.invoice_serie)

    def __braspress_tracking(self,_taxvat:str,_invoice:str):
        #ignora a verificacao de certificado SSL
        self.nav.verify = False
        self.nav.headers = {
            # "Authorization": ConfigBraspress.TOKEN_TYPE.value+" "+ConfigBraspress.TOKEN_ACCESS.value
            "Authorization": environ.get("BRASPRESS_TOKEN_TYPE")+" "+environ.get("BRASPRESS_TOKEN_ACCESS")
        }
        resp = self.nav.get('https://api.braspress.com/v'+environ.get("BRASPRESS_API_VERSION")+'/tracking/byNf/'+_taxvat+'/'+_invoice+'/json')
        if resp.status_code==200:
            consulta = resp.json()

            # for con in consulta['conhecimentos']:
            #     retb = "<h6 class='mb-2 text-secondary'>Transportadora: BRASPRESS</h6><ul class='timeline'>"
            #     for tml in con['timeLine']:
            #         retb += """<li><p class='card-text'><span class='text-danger'>{data}</span><br>Status: {status}</p></li>
            #         """.format(status=tml['descricao'],data=datetime.strptime(tml['data'],"%Y-%m-%d").strftime("%d/%m/%Y"))
            #     retb += "<li><p class='card-text'><span class='text-danger'>{data}</span><br>Status: {status}</p></li>".format(data=datetime.strptime(con['previsaoEntrega'],"%Y-%m-%d").strftime("%d/%m/%Y"),status="Previsão de Entrega")
            # retb += "</ul>"
            
            return [{
                "shipping": "BRASPRESS",
                "forecast": datetime.strptime(con['previsaoEntrega'],"%Y-%m-%d").strftime("%d/%m/%Y"),
                "timeline":[{
                    "date": datetime.strptime(tml['data'],"%Y-%m-%d").strftime("%d/%m/%Y"),
                    "status": tml["descricao"]
                }for tml in con["timeLine"]]
            }for con in consulta['conhecimentos']]
        
        return False

    def __jadlog_tracking(self,_nf:str,_nf_serie:str,_cnpj:str):
        self.nav.verify = False
        self.nav.headers = {
            # "Authorization": ConfigJadlog.TOKEN_TYPE.value+" "+ConfigJadlog.TOKEN_ACCESS.value,
            "Authorization": environ.get("JADLOG_TOKEN_TYPE")+" "+environ.get("JADLOG_TOKEN_ACCESS"),
            "Content-Type": "application/json"
        }
        resp = self.nav.get('https://jadlog.com.br/api/tracking/consultar',params={
            "consulta":[{
                "df":{
                    "nf": _nf,
                    "serie": _nf_serie,
                    "tpDocumento": 2,
                    "cnpjRementente": _cnpj
                }
            }]
        })
        if resp.status_code==200:
            consulta = resp.json()
            #realizar o retorno em formato HTML em um card
            
            # ret = "<h6 class='mb-2 text-secondary'>Transportadora: JADLOG</h6><ul class='timeline'>"
            # for cons in consulta['consulta']:
            #     for evt in cons['tracking']['eventos']:
            #         ret += """<li><p class='card-text'><span class='text-danger'>{data}</span><br>Status: {status}</p></li>
            #         """.format(status=evt['status'],data=datetime.strptime(evt['data'],"%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S"))
            #     ret += "<li><p class='card-text'><span class='text-danger'>{data}</span><br/>Status: {status}</p></li>".format(data=datetime.strptime(cons['previsaoEntrega'],"%Y-%m-%d").strftime("%d/%m/%Y"),status="Previsão de Entrega")
            # ret += "</ul>"

            return [{
                "shipping":"JADLOG",
                "forecast": datetime.strptime(cons['previsaoEntrega'],"%Y-%m-%d").strftime("%d/%m/%Y"),
                "timeline": [{
                    "date": datetime.strptime(evt['data'],"%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M"),
                    "status": evt['status']
                }for evt in cons['tracking']['eventos']]
            }for cons in consulta['consulta']]
        return False

    def __jamef_login(self):
        resp = self.nav.post('https://developers.jamef.com.br/login',
                      data={
                        "username": environ.get("JAMEF_USERNAME"), # ConfigJamef.USERNAME.value,
                        "password": environ.get("JAMEF_PASSWORD") # ConfigJamef.PASSWORD.value
                      }
                      )
        if resp.status_code==200:
            return resp.json()
        return False

    def __jamef_tracking(self,_cnpj:str,_nf:str,_serie_nf:str):
        login = self.__jamef_login()
        if login!=False:
            self.nav.verify = False
            self.nav.headers = {
                "Authorization": login.token_type+" "+login.access_token
            }
            resp = self.nav.post('https://developers.jamef.com.br/rastreamento/ver',data={
                {
                    "documentoResponsavelPagamento" : str(environ.get("F2B_COMPANY_TAXVAT")),
                    "documentoDestinatario": _cnpj,
                    "numeroNotaFiscal": _nf,
                    "numeroSerieNotaFiscal": _serie_nf
                }
            })
            if resp.status_code==200:
                consulta = resp.json()

                # retj = "<h6 class='mb-2 text-secondary'>Transportadora: JAMEF</h6><ul class='timeline'>"
                # for cons in consulta['conhecimentos']:
                #         for evt in cons['historico']:
                #             retj += """<li><p class='card-text'><span class='text-danger'>{data}</span><br>Status: {status}</p></li>
                #             """.format(status=evt['statusRastreamento'],data=datetime.strptime(evt['dataAtualizacao'],"%d/%m/%y %H:%M").strftime("%d/%m/%Y %H:%M"))
                #         retj += "<li><p class='card-text'><span class='text-danger'>{data}</span><br>Status: {status}</p></li>".format(data=datetime.strptime(cons['dataPrevisaoEntrega'],"%d/%m/%y").strftime("%d/%m/%Y"),status="Previsão de Entrega")
                # retj += "</ul>"

                return [{
                    "shipping": "JAMEF",
                    "forecast": datetime.strptime(cons['dataPrevisaoEntrega'],"%d/%m/%y").strftime("%d/%m/%Y"),
                    "timeline":[{
                        "date": datetime.strptime(evt['dataAtualizacao'],"%d/%m/%y %H:%M").strftime("%d/%m/%Y %H:%M"),
                        "status": evt['statusRastreamento']
                    }for evt in cons['historico']]
                }for cons in consulta['conhecimentos']]
        return False
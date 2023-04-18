from config import Config,ShippingCompany,ConfigBraspress,ConfigJadlog,ConfigJamef
import requests
import urllib3
from datetime import datetime

class Shipping():
    nav = None
    cfg = None
    shp = None
    def __init__(self,_cfg:Config) -> None:
        #remove o warning de excessao da verificacao do certificado SSL
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.nav = requests.Session()
        self.cfg = _cfg

    def tracking(self,_shp:ShippingCompany,options):
        if _shp==ShippingCompany.BRASPRESS:
            return self.__braspress_tracking()
        if _shp==ShippingCompany.JADLOG:
            return self.__jadlog_tracking()
        if _shp==ShippingCompany.JAMEF:
            return self.__jamef_tracking()

    def __braspress_tracking(self,_taxvat:str,_invoice:str):
        #ignora a verificacao de certificado SSL
        self.nav.verify = False
        self.nav.headers = {
            "Authorization": ConfigBraspress.TOKEN_TYPE.value+" "+ConfigBraspress.TOKEN_ACCESS.value
        }
        resp = self.nav.get('https://api.braspress.com/v'+ConfigBraspress.API_VERSION.value+'/tracking/byNf/'+_taxvat+'/'+_invoice+'/json')
        if resp.status_code==200:
            consulta = resp.json()

            for con in consulta['conhecimentos']:
                retb = """<h6 class='mb-2 text-secondary'>Transportadora: BRASPRESS</h6>
                    <ul class='timeline'>"""
                for tml in con['timeLine']:
                    retb += """<li>
                        <p class='card-text'><span class='text-danger'>{data}</span><br>Status: {status}</p>
                    </li>
                    """.format(status=tml['descricao'],data=datetime.strptime(tml['data'],"%Y-%m-%d").strftime("%d/%m/%Y"))
                retb += """<li><p class='card-text'><span class='text-danger'>{data}</span><br>Status: {status}</p></li>""".format(data=datetime.strptime(con['previsaoEntrega'],"%Y-%m-%d").strftime("%d/%m/%Y"),status="Previsão de Entrega")
            retb += """</ul>"""

            return retb
        
        return False

    def __jadlog_tracking(self,_nf:str,_nf_serie:str,_cnpj:str):
        self.nav.verify = False
        self.nav.headers = {
            "Authorization": ConfigJadlog.TOKEN_TYPE.value+" "+ConfigJadlog.TOKEN_ACCESS.value,
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
            
            ret = """<h6 class='mb-2 text-secondary'>Transportadora: JADLOG</h6>
                    <ul class='timeline'>"""
            for cons in consulta['consulta']:
                for evt in cons['tracking']['eventos']:
                    ret += """<li><p class='card-text'><span class='text-danger'>{data}</span><br>Status: {status}</p></li>
                    """.format(status=evt['status'],data=datetime.strptime(evt['data'],"%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S"))
                ret += "<li><p class='card-text'><span class='text-danger'>{data}</span><br/>Status: {status}</p></li>".format(data=datetime.strptime(cons['previsaoEntrega'],"%Y-%m-%d").strftime("%d/%m/%Y"),status="Previsão de Entrega")

            ret += """</ul>"""

            return ret
        return False

    def __jamef_login(self):
        resp = self.nav.post('https://developers.jamef.com.br/login',
                      data={
                        "username": ConfigJamef.USERNAME.value,
                        "password": ConfigJamef.PASSWORD.value
                      }
                      )
        if resp.status_code==200:
            return True
        return False

    def __jamef_tracking(self):
        login = self.__jamef_login()
        if login!=False:
            self.nav.verify = False
            self.nav.headers = {
                "Authorization": login.token_type+" "+login.token_access
            }
            resp = self.nav.post('https://developers.jamef.com.br/rastreamento/ver')
            if resp.status_code==200:
                return resp.json()
        return False





# export class ShippingService{
#   sys_config:any = (configData as any).default;
#   constructor(private http:HttpClient) { }

#   trackingBraspress(cnpj:string,notaFiscal:string):Observable<BraspressReturn>{
#     //https://api.braspress.com/home

#     const httpHeader:HttpHeaders = new HttpHeaders().set('Authorization','Basic '+this.sys_config.integrations.braspress.api_token);
#     return this.http.get<BraspressReturn>('https://api.braspress.com/v'+this.sys_config.integrations.braspress.api_version+'/tracking/'+cnpj+'/'+notaFiscal+'/json',{
#       headers:httpHeader
#     });
#   }

#   trackingJadlog():Observable<JadlogReturn>{
#     const httpHeader:HttpHeaders = new HttpHeaders()
#       .set('Authorization','Bearer '+this.sys_config.integration.jadlog.api_token)
#       .set('Content-Type',"application\json");
#     //https://www.jadlog.com.br/jadlog/arquivos/api_integracao.pdf
#     return this.http.post<JadlogReturn>('http://www.jadlog.com.br/embarcador/api/tracking/consultar',{
#       headers:httpHeader
#     })
#   }

#   loginJamef():Observable<JamefToken>{
#     const myParams:HttpParams = new HttpParams()
#       .set('username',this.sys_config.integration.jamef.username)
#       .set('password',this.sys_config.integration.jamef.password);

#     return this.http.post<JamefToken>('https://developers.jamef.com.br/login',{
#       httpParams: myParams
#     });
#   }

#   trackingJamef(token_type:string,token_access:string):Observable<JamefReturn>{
#     const myParams: HttpParams = new HttpParams()
#           .set('Authorization',token_type+' '+token_access);
#     return this.http.post<JamefReturn>('https://developers.jamef.com.br/login/rastreamento/ver',{
#           httpParams: myParams
#         });
#     //https://developers.jamef.com.br/documentacao
#   }


# }
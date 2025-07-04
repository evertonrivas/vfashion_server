from http import HTTPStatus
import importlib
from flask_restx import Resource,Namespace,fields
from flask import request
from os import environ
from f2bconfig import DashboardImage, DashboardImageColor

ns_config = Namespace("config",description="Obtem as configuracoes do sistema")

#API Models
cfg_model = ns_config.model(
    "Config",{
        "use_company_custom":fields.Boolean,
        "company_name":fields.String,
        "company_logo":fields.String,
        "company_instagram":fields.String,
        "company_facebook":fields.String,
        "company_linkedin":fields.String,
        "company_max_up_files":fields.Integer,
        "company_max_up_images":fields.Integer,
        "company_use_url_images":fields.Boolean,
        "system_pagination_size":fields.Integer,
    }
)

cfg_cep_model = ns_config.model(
    "Cep",{
        "postal_code": fields.String
    }
)

@ns_config.route("/")
class CategoryList(Resource):
    @ns_config.response(HTTPStatus.OK.value,"Obtem as configurações do sistema",cfg_model)
    @ns_config.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    def get(self):
        try:
            if environ.get("F2B_DASHBOARD_CONFIG")=="MEN":
                dashboard = DashboardImage.MEN.value
                dashcolor = DashboardImageColor.MEN.value
            elif environ.get("F2B_DASHBOARD_CONFIG")=="WOMEN":
                dashboard = DashboardImage.WOMEN.value
                dashcolor = DashboardImageColor.WOMEN.value
            elif environ.get("F2B_DASHBOARD_CONFIG")=="WHEAT":
                dashboard = DashboardImage.WHEAT.value
                dashcolor = DashboardImageColor.WHEAT.value
            elif environ.get("F2B_DASHBOARD_CONFIG")=="DRINK":
                dashboard = DashboardImage.DRINK.value
                dashcolor = DashboardImageColor.DRINK.value
            elif environ.get("F2B_DASHBOARD_CONFIG")=="SHOES":
                dashboard = DashboardImage.SHOES.value
                dashcolor = DashboardImageColor.SHOES.value
            elif environ.get("F2B_DASHBOARD_CONFIG")=="PISTON":
                dashboard = DashboardImage.PISTON.value
                dashcolor = DashboardImageColor.PISTON.value
            else:
                dashboard = DashboardImage.PHARMA.value
                dashcolor = DashboardImageColor.PHARMA.value

            return {
                "company_dashboard_color": dashcolor,
                "company_dashboard_image": dashboard,
                "company_facebook": environ.get("F2B_COMPANY_FACEBOOK"),
                "company_instagram": environ.get("F2B_COMPANY_INSTAGRAM"),
                "company_linkedin": environ.get("F2B_COMPANY_LINKEDIN"),
                "company_logo": environ.get("F2B_COMPANY_LOGO"),
                "company_max_up_files": int(str(environ.get("F2B_COMPANY_MAX_UP_FILES"))),
                "company_max_up_images": int(str(environ.get("F2B_COMPANY_MAX_UP_IMAGES"))),
                "company_use_url_images": True if environ.get("F2B_COMPANY_USE_URL_IMAGES")=="1" else False,
                "company_name": environ.get("F2B_COMPANY_NAME"),
                "flimv_model": environ.get("F2B_FLIMV_MODEL"),
                "system_pagination_size": int(str(environ.get("F2B_PAGINATION_SIZE"))),
                "use_company_custom": True if environ.get("F2B_COMPANY_CUSTOM")=="1" else False,
            }
        except Exception as e:
            return {
                "error_code": e.args.count,
                "error_details": e.args[0],
                "error_sql": None
            }
    
    @ns_config.response(HTTPStatus.OK.value,"Obtem as informações de CEP")
    @ns_config.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_config.doc(body=cfg_cep_model,description="Dados necessários",name="content")
    def post(self):
        try:
            req = request.get_json()
            module = str(environ.get("F2B_CEP_MODULE"))
            class_name = str(environ.get("F2B_CEP_MODULE")).replace("_"," ").title().replace(" ","")
            CEP_OBJ = getattr(
            importlib.import_module('integrations.cep.'+module),
            class_name
            )
            cep = CEP_OBJ()
            return cep.get_postal_code(req["postal_code"])
        except Exception:
            return False
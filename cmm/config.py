from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from auth import auth
from os import environ

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
        "system_pagination_size":fields.Integer
    }
)

@ns_config.route("/")
class CategoryList(Resource):
    @ns_config.response(HTTPStatus.OK.value,"Obtem as configurações do sistema",cfg_model)
    @ns_config.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    def get(self):
        try:
            return {
                "system_pagination_size": int(environ.get("F2B_PAGINATION_SIZE")),
                "use_company_custom": True if environ.get("F2B_COMPANY_CUSTOM")=="1" else False,
                "company_name": environ.get("F2B_COMPANY_NAME"),
                "company_logo": environ.get("F2B_COMPANY_LOGO"),
                "company_instagram": environ.get("F2B_COMPANY_INSTAGRAM"),
                "company_facebook": environ.get("F2B_COMPANY_FACEBOOK"),
                "company_linkedin": environ.get("F2B_COMPANY_LINKEDIN"),
                "company_max_up_files": int(environ.get("F2B_COMPANY_MAX_UP_FILES")),
                "company_max_up_images": int(environ.get("F2B_COMPANY_MAX_UP_IMAGES")),
                "company_use_url_images": True if environ.get("F2B_COMPANY_USE_URL_IMAGES")=="1" else False
            }
        except Exception as e:
            return {
                "error_code": e.args.count,
                "error_details": e.args[0],
                "error_sql": ''
            }
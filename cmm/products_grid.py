from http import HTTPStatus
import json
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmProductsGrid,CmmProductsGridDistribution, _get_params,db
from sqlalchemy import Select, asc, desc, exc, and_
from auth import auth
from config import Config

ns_gprod = Namespace("products-grid",description="Operações para manipular dados das grades de produtos")

grd_pag_model = ns_gprod.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

grd_dist_model = ns_gprod.model(
    "Distribution",{
        "size": fields.String,
        "color": fields.String,
        "value": fields.Integer,
        "is_percent": fields.Boolean
    }
)

grd_model = ns_gprod.model(
    "Grid",{
        "id": fields.Integer,
        "name": fields.String,
        "distribution": fields.List(fields.Nested(grd_dist_model))
    }
)

grd_return = ns_gprod.model(
    "GridReturn",{
        "pagination": fields.Nested(grd_pag_model),
        "data": fields.List(fields.Nested(grd_model))
    }
)


@ns_gprod.route("/")
class GridList(Resource):

    @ns_gprod.response(HTTPStatus.OK.value,"Obtem os registros de grades existentes",grd_return)
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_gprod.param("page","Número da página de registros","query",type=int,required=True)
    @ns_gprod.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_gprod.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = Config.PAGINATION_SIZE.value if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query    = None if request.args.get("query") is None else request.args.get("query")

        try:
            params    = _get_params(query)
            trash     = False if hasattr(params,'trash')==False else True
            list_all  = False if hasattr(params,"list_all")==False else True
            order_by  = "id" if hasattr(params,"order_by")==False else params.order_by
            direction = desc if hasattr(params,"order_dir") == 'DESC' else asc

            filter_search   = None if hasattr(params,"search")==False else params.search
            filter_default  = None if hasattr(params,"default")==False else params.default

            rquery = Select(CmmProductsGrid.id,
                            CmmProductsGrid.origin_id,
                            CmmProductsGrid.name,
                            CmmProductsGrid.default,
                            CmmProductsGrid.date_created,
                            CmmProductsGrid.date_updated)\
                            .where(CmmProductsGrid.trash==trash)\
                            .order_by(direction(getattr(CmmProductsGrid,order_by)))

            if filter_search is not None:
                rquery = rquery.where(CmmProductsGrid.name.like("%{}%".format(filter_search)))

            if filter_default is not None:
                rquery = rquery.where(CmmProductsGrid.default==filter_default)

            if list_all==False:
                pag    = db.paginate(rquery,page=pag_num,per_page=pag_size)
                rquery = rquery.limit(pag_size).offset((pag_num - 1) * pag_size)
                return {
                    "pagination":{
                        "registers": pag.total,
                        "page": pag_num,
                        "per_page": pag_size,
                        "pages": pag.pages,
                        "has_next": pag.has_next
                    },
                    "data":[{
                        "id": m.id,
                        "origin_id":m.origin_id,
                        "name": m.name,
                        "default": m.default,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    }for m in db.session.execute(rquery)]
                }
            else:
                return [{
                        "id": m.id,
                        "origin_id": m.origin_id,
                        "name": m.name,
                        "default": m.default,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated!=None else None
                    }for m in db.session.execute(rquery)]
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    def get_grid_distribution(self,id:int):
        rquery = CmmProductsGridDistribution.query.find_by(id_grid=id)
        return [{
            "size": m.size,
            "color": m.color,
            "value": m.value,
            "is_percent": m.is_percent
        } for m in rquery]


    @ns_gprod.response(HTTPStatus.OK.value,"Cria uma nova grade no sistema")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar nova grade!")
    @ns_gprod.doc(body=grd_model)
    @auth.login_required
    def post(self)->int:
        try:
            req = json.dumps(request.get_json())
            grid = CmmProductsGrid()
            grid.name = req.name
            db.session.add(grid)
            db.session.commit()

            for dist in req.distribution:
                gridd         = CmmProductsGridDistribution()
                gridd.id_grid = grid.id
                gridd.color   = dist.color
                gridd.size    = dist.size
                gridd.value   = dist.value
                gridd.is_percent = dist.is_percent
                db.session.add(gridd)
                db.session.commit()

            return grid.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


@ns_gprod.route("/<int:id>")
@ns_gprod.param("id","Id do registro")
class GridApi(Resource):
    @ns_gprod.response(HTTPStatus.OK.value,"Obtem um registro de uma grade",grd_model)
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            grid = CmmProductsGrid.query.get(id)
            dist = CmmProductsGridDistribution.query.find_by(id_grid=id)
            return {
                "id": id,
                "name": grid.name,
                "distribution":[{
                    "size": m.size,
                    "color": m.color,
                    "value": m.value,
                    "is_percent": m.is_percent
                } for m in dist]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_gprod.response(HTTPStatus.OK.value,"Salva dados de uma grade")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int)->bool:
        try:
            req = json.dumps(request.get_json())
            grid = CmmProductsGrid.query.get(id)
            grid.name = grid.name if req.name is None else req.name
            grid.trash = grid.trash if req.trash is None else req.trash
            db.session.commit()

            #apaga e recria as distribuicoes
            db.session.delete(CmmProductsGridDistribution()).where(CmmProductsGridDistribution().id_grid==id)
            db.session.commit()
            for dist in grid.distribution:
                gridd         = CmmProductsGridDistribution()
                gridd.id_grid = id
                gridd.color   = dist.color
                gridd.size    = dist.size
                gridd.value   = dist.value
                gridd.is_percent = dist.is_percent
                db.session.add(gridd)
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_gprod.response(HTTPStatus.OK.value,"Exclui os dados de uma grade")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int)->bool:
        try:
            grid       = CmmProductsGrid.query.get(id)
            grid.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
from auth import auth
from os import environ
from flask import request
from http import HTTPStatus
from models.helpers import _get_params, db
from flask_restx import Resource,Namespace,fields
from sqlalchemy import Delete, Select, asc, desc, exc
from models.tenant import CmmProductsGridSizes, CmmTranslateSizes
from models.tenant import CmmProductsGrid,CmmProductsGridDistribution

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

    @ns_gprod.response(HTTPStatus.OK,"Obtem os registros de grades existentes",grd_return)
    @ns_gprod.response(HTTPStatus.BAD_REQUEST,"Falha ao listar registros!")
    @ns_gprod.param("page","Número da página de registros","query",type=int,required=True)
    @ns_gprod.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_gprod.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(str(request.args.get("page")))
        pag_size = int(str(environ.get("F2B_PAGINATION_SIZE"))) if request.args.get("pageSize") is None else int(str(request.args.get("pageSize")))
        query    = None if request.args.get("query") is None else request.args.get("query")

        try:
            params    = _get_params(query)
            trash     = False if not hasattr(params,'trash') else True
            list_all  = False if not hasattr(params,"list_all") else True
            order_by  = "id" if not hasattr(params,"order_by") else params.order_by if params is not None else 'id'
            direction = desc if hasattr(params,"order_dir") == 'DESC' else asc

            filter_search   = None if not hasattr(params,"search") else params.search if params is not None else None
            # filter_default  = None if not hasattr(params,"default") else params.default

            rquery = Select(CmmProductsGrid.id,
                            CmmProductsGrid.name,
                            CmmProductsGrid.date_created,
                            CmmProductsGrid.date_updated)\
                            .where(CmmProductsGrid.trash==trash)\
                            .order_by(direction(getattr(CmmProductsGrid,order_by)))

            if filter_search is not None:
                rquery = rquery.where(CmmProductsGrid.name.like("%{}%".format(filter_search)))

            # if filter_default is not None:
            #     rquery = rquery.where(CmmProductsGrid.default==filter_default)

            if not list_all:
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
                        "name": m.name,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
                    }for m in db.session.execute(rquery)]
                }
            else:
                return [{
                        "id": m.id,
                        "name": m.name,
                        "date_created": m.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                        "date_updated": m.date_updated.strftime("%Y-%m-%d %H:%M:%S") if m.date_updated is not None else None
                    }for m in db.session.execute(rquery)]
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_gprod.response(HTTPStatus.OK,"Cria uma nova grade no sistema")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST,"Falha ao criar nova grade!")
    @ns_gprod.doc(body=grd_model)
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()

            grid = CmmProductsGrid()
            grid.name = req["name"]
            db.session.add(grid)
            db.session.commit()

            for size in req["sizes"]:
                grids:CmmProductsGridSizes = CmmProductsGridSizes()
                grids.id_size = size
                grids.id_grid = grid.id
                db.session.add(grids)
            db.session.commit()

            return grid.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_gprod.response(HTTPStatus.OK,"Exclui os dados de uma grade")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            for id in req["ids"]:
                grid = CmmProductsGrid.query.get(id)
                setattr(grid,"trash",req["toTrash"])
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


@ns_gprod.route("/<int:id>")
@ns_gprod.param("id","Id do registro")
class GridApi(Resource):
    @ns_gprod.response(HTTPStatus.OK,"Obtem um registro de uma grade",grd_model)
    @ns_gprod.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            grid:CmmProductsGrid|None = CmmProductsGrid.query.get(id)
            if grid is None:
                return {
                    "error_code": HTTPStatus.BAD_REQUEST.value,
                    "error_details": "Registro não encontrado!",
                    "error_sql": ""
                }, HTTPStatus.BAD_REQUEST
            ssmtm = Select(CmmProductsGridSizes.id_size).where(CmmProductsGridSizes.id_grid==id)
            return {
                "id": id,
                "name": grid.name,
                "sizes":[{
                    "id": s.id_size
                }for s in db.session.execute(ssmtm)]
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_gprod.response(HTTPStatus.OK,"Salva dados de uma grade")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            req = request.get_json()
            grid:CmmProductsGrid|None = CmmProductsGrid.query.get(id)
            if grid is not None:
                grid.name    = req["name"]
                db.session.commit()

            # remove todos os tamanhos existentes para garantir a consistencia da atualizacao
            db.session.execute(Delete(CmmProductsGridSizes).where(CmmProductsGridSizes.id_grid==id))
            db.session.commit()

            for size in req["sizes"]:
                grids:CmmProductsGridSizes = CmmProductsGridSizes()
                grids.id_size = size
                setattr(grids,"id_grid",(0 if grid is None else grid.id))
                db.session.add(grids)
            db.session.commit()

            # faz a adequacao em relacao aos tamanhos da grade
            db.session.execute(Delete(CmmProductsGridDistribution).where(CmmProductsGridDistribution.id_size.in_(req["sizes"])))
            db.session.commit()

            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
class GridDistribution(Resource):
    @ns_gprod.response(HTTPStatus.OK,"Lista os dados de uma distribuição de uma grade")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int):
        try:
            stmt = Select(CmmProductsGridSizes.id_size,
                          CmmTranslateSizes.name,
                          CmmTranslateSizes.new_size,
                          CmmProductsGridDistribution.value)\
                .join(CmmTranslateSizes,CmmTranslateSizes.id==CmmProductsGridSizes.id_size)\
                .outerjoin(CmmProductsGridDistribution,CmmProductsGridDistribution.id_size==CmmTranslateSizes.id)\
                .where(CmmProductsGridSizes.id_grid==id)
            
            return [{
                "id": s.id_size,
                "name": s.name,
                "new_size": s.new_size,
                "value": 0 if s.value is None else int(s.value),
            }for s in db.session.execute(stmt)]
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    @ns_gprod.response(HTTPStatus.OK,"Salva dados de uma grade")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required
    def post(self,id:int):
        try:
            req  = request.get_json()
            for size in req:
                dist = CmmProductsGridDistribution.query.get((id,size["id"]))
                if dist is not None:
                    dist.value = size["value"]
                else:
                    dist:CmmProductsGridDistribution|None = CmmProductsGridDistribution()
                    setattr(dist,"id_grid",id)
                    setattr(dist,"id_size",int(size["id"]))
                    setattr(dist,"value",int(size["value"]))
                    db.session.add(dist)
                db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_gprod.response(HTTPStatus.OK,"Salva dados de uma grade")
    @ns_gprod.response(HTTPStatus.BAD_REQUEST,"Registro não encontrado!")
    @auth.login_required 
    def delete(self,id:int):
        try:
            db.session.execute(Delete(CmmProductsGridDistribution).where(
                CmmProductsGridDistribution.id_grid==id
            ))
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
ns_gprod.add_resource(GridDistribution,'/distribution/<int:id>')
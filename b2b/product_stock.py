from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bProductStock, CmmTranslateColors, CmmTranslateSizes, db
from sqlalchemy import Select, and_, exc,or_,desc,asc
from auth import auth

ns_stock = Namespace("product-stock",description="Operações para manipular dados de estoques de produtos")

stock_pag_model = ns_stock.model(
    "Pagination",{
        "registers": fields.Integer,
        "page": fields.Integer,
        "per_page": fields.Integer,
        "pages": fields.Integer,
        "has_next": fields.Boolean
    }
)

stock_model = ns_stock.model(
    "ProductStock",{
        "id_product": fields.Integer,
        "color": fields.String,
        "size": fields.String,
        "quantity": fields.Integer,
        "limited": fields.Boolean
    }
)

stock_return = ns_stock.model(
    "ProductStockReturn",{
        "pagination": fields.Nested(stock_pag_model),
        "data": fields.List(fields.Nested(stock_model))
    }
)


@ns_stock.route("/")
class ProductStockList(Resource):
    @ns_stock.response(HTTPStatus.OK.value,"Obtem a lista de estoques de produtos do B2B",stock_return)
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @ns_stock.param("page","Número da página de registros","query",type=int,required=True)
    @ns_stock.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_stock.param("query","Texto para busca","query")
    @ns_stock.param("list_all","Ignora as paginas e lista todos os registros",type=bool,default=False)
    @ns_stock.param("order_by","Campo de ordenacao","query")
    @ns_stock.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        pag_num    =  1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size   = 25 if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        search     = "" if request.args.get("query") is None else "{}%".format(request.args.get("query"))
        list_all   = False if request.args.get("list_all") is None else True
        order_by   = "id" if request.args.get("order_by") is None else request.args.get("order_by")
        direction  = desc if request.args.get("order_dir") == 'DESC' else asc

        try:
            if search=="":
                rquery = B2bProductStock\
                    .query\
                    .filter(or_(B2bProductStock.color.like(search),B2bProductStock.size.like(search)))\
                    .order_by(direction(getattr(B2bProductStock, order_by)))
            else:
                rquery = B2bProductStock\
                    .query\
                    .order_by(direction(getattr(B2bProductStock, order_by)))

            if list_all==False:
                rquery.paginate(page=pag_num,per_page=pag_size)

                retorno =  {
                    "pagination":{
                        "registers": rquery.total,
                        "page": pag_num,
                        "per_page": pag_size,
                        "pages": rquery.pages,
                        "has_next": rquery.has_next
                    },
                    "data":[{
                        "id_product":m.id_product,
                        "color": m.color,
                        "size": m.size,
                        "quantity": m.quantity,
                        "limited": m.limited
                    } for m in rquery.items]
                }
            else:
                retorno = [{
                        "id_product":m.id_product,
                        "color": m.color,
                        "size": m.size,
                        "quantity": m.quantity,
                        "limited": m.limited
                    } for m in rquery]
                
            return retorno
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_stock.response(HTTPStatus.OK.value,"Cria um registro de estoque de produto do B2B")
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Falha ao criar nova condicao de pagamento!")
    @ns_stock.param("name","Nome da condição de pagamento","formData",required=True)
    @ns_stock.param("received_days","Dias para recebimento","formData",type=int,required=True)
    @ns_stock.param("installments","Número de parcelas","formData",type=int,required=True)
    @auth.login_required
    def post(self)->int:
        try:
            stock = B2bProductStock()
            stock.id_product = int(request.form.get("id_product"))
            stock.color      = request.form.get("color")
            stock.size       = request.form.get("size")
            stock.quantity   = int(request.form.get("quantity"))
            stock.limited    = bool(request.form.get("limited"))
            db.session.add(stock)
            db.session.commit()
            return stock.id
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

@ns_stock.route("/<int:id>")
@ns_stock.param("id","Id do produto")
@ns_stock.param("color","Cor do produto")
@ns_stock.param("size","Tamanho do produto")
class ProductStockApi(Resource):
    @ns_stock.response(HTTPStatus.OK.value,"Obtem um registro do estoque de um produto do B2B",stock_model)
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def get(self,id:int,color:str,size:str):
        try:
            return B2bProductStock.query.get([id,color,size]).to_dict()
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    @ns_stock.response(HTTPStatus.OK.value,"Salva dados de uma condição de pgamento")
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @ns_stock.param("quantiy","Quantidade do estoque","formData",required=True)
    @ns_stock.param("limited","Se o produto é limitado","formData",type=bool,required=True)
    @auth.login_required
    def post(self,id:int,color:str,size:str)->bool:
        try:
            stock = B2bProductStock.query.get([id,color,size])
            stock.quantity = stock.quantity if request.form.get("quantity") is None else int(request.form.get("quantity"))
            stock.limited  = stock.limited if request.form.get("limited") is None else bool(request.form.get("limited"))
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
    
    @ns_stock.response(HTTPStatus.OK.value,"Exclui os dados de uma condição de pagamento")
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Registro não encontrado!")
    @auth.login_required
    def delete(self,id:int,color:str,size:str)->bool:
        try:
            payCond = B2bProductStock.query.get([id,color,size])
            payCond.trash = True
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

class ProductStockLoad(Resource):
    @ns_stock.response(HTTPStatus.OK.value,"Obtem a lista de estoques de um determinado produto do B2B")
    @ns_stock.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros!")
    @auth.login_required
    def get(self,id_product:int):    
        cquery = Select(B2bProductStock.color,CmmTranslateColors.hexcode,CmmTranslateColors.name)\
            .distinct(B2bProductStock.color)\
            .join(CmmTranslateColors,CmmTranslateColors.color==B2bProductStock.color)\
            .filter(B2bProductStock.id_product==id_product)\
            .order_by(asc(B2bProductStock.color))

        cquery = db.session.execute(cquery)
        
        return [{
            "color_name": m.name,
            "color_hexa": m.hexcode,
            "color_code": m.color,
            "sizes": self.get_sizes(id_product,m.color)
        }for m in cquery]
    
    def get_sizes(self,id_product:int,color:str):
        subquery = Select(B2bProductStock.quantity,B2bProductStock.limited,B2bProductStock.size.label("size_code"))\
            .where(and_(B2bProductStock.id_product==id_product,B2bProductStock.color==color))\
            .cte()
        query = Select(CmmTranslateSizes.size.label("size_code"),CmmTranslateSizes.size_name,subquery.c.quantity,subquery.c.limited)\
            .outerjoin(subquery,subquery.c.size_code==CmmTranslateSizes.size)
        
        #print(query)

        query = db.session.execute(query)

        return [{
                "size_code": s.size_code,
                "size_name": s.size_name,
                "size_value": self.formatQuantity(s.quantity,s.limited)
            }for s in query]
    
    def formatQuantity(self,quantity:int,limited:bool):
        if quantity is None and limited==False:
            return 99999
        if quantity is None  and limited is None:
            return None
        return quantity


ns_stock.add_resource(ProductStockLoad,"/load-by-product/<int:id_product>")
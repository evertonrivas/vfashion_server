
from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bCartShopping, CmmProducts, CmmTranslateColors, CmmTranslateSizes,CmmProductsImages, db
from sqlalchemy import exc,Select,and_,func,tuple_,distinct,desc,asc,Delete
from auth import auth
from config import Config

ns_cart = Namespace("cart",description="Operações para manipular dados do carrinho de compras")

@ns_cart.route("/")
class CartApi(Resource):
    @ns_cart.response(HTTPStatus.OK.value,"Retorna os dados de produtos que estão no carrinho de compras")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros")
    @ns_cart.param("id_profile","Número da página de registros","query",type=int,required=True,default=1)
    @ns_cart.param("order_by","Campo de ordenacao","query")
    @ns_cart.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        id_profile  =  int(request.args.get("id_profile"))
        order_by   = "id_product" if request.args.get("order_by") is None else request.args.get("order_by")
        direction  = desc if request.args.get("order_dir") == 'DESC' else asc

        try:
            
            pquery = Select(B2bCartShopping.id_product,
                            B2bCartShopping.price,
                            CmmProductsImages.img_url,
                            CmmProducts.name,CmmProducts.refCode,
                            func.sum(B2bCartShopping.quantity).label("total")).distinct()\
                .join(CmmProductsImages,and_(CmmProductsImages.id_product==B2bCartShopping.id_product,CmmProductsImages.img_default==True))\
                .join(CmmProducts,CmmProducts.id==B2bCartShopping.id_product)\
                .where(B2bCartShopping.id_customer==id_profile)\
                .group_by(B2bCartShopping.id_product)\
                .order_by(direction(getattr(B2bCartShopping,order_by)))
            
            return [{
                "id_product": m.id_product,
                "ref": m.refCode,
                "name": m.name,
                "img_url": m.img_url,
                "price_un": str(m.price),
                "itens": str(m.total),
                "total_price": str(m.total*m.price),
                "colors":[{
                    "name": c.name,
                    "hexa": c.hexcode,
                    "code": c.color,
                    "sizes":[{
                        "name": s.size_name,
                        "quantity": int(0 if s.quantity is None else s.quantity)
                    } for s in self.get_sizes(id_profile,m.id_product,c.color)]
                }for c in self.get_colors(id_profile,m.id_product)]
            } for m in db.session.execute(pquery).all()]

        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    def get_colors(self,id_customer:int,id_product:int):
        return db.session.execute(Select(B2bCartShopping.color,CmmTranslateColors.hexcode,CmmTranslateColors.name).distinct()\
                .join(CmmTranslateColors,CmmTranslateColors.color==B2bCartShopping.color)\
                .where(and_(B2bCartShopping.id_customer==id_customer,
                            B2bCartShopping.id_product==id_product))).all()

    def get_sizes(self,id_customer:int,id_product:int,color:str):
        subquery = Select(
            B2bCartShopping.size.label("size_code"),
            B2bCartShopping.quantity)\
            .where(and_(B2bCartShopping.id_customer==id_customer,B2bCartShopping.id_product==id_product,B2bCartShopping.color==color)).cte()

        return db.session.execute(Select(CmmTranslateSizes.size_name,subquery.c.size_code,subquery.c.quantity).distinct()\
            .outerjoin(subquery,subquery.c.size_code==CmmTranslateSizes.size)).all()
    

    @ns_cart.response(HTTPStatus.OK.value,"Retorna verdadeiro ou falso se conseguiu excluir o(s) registro(s)")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Falha ao excluir")
    @auth.login_required
    def delete(self):
        try:
            ids = request.get_json()
            stmt = Delete(B2bCartShopping).where(B2bCartShopping.id_product.in_(ids))
            db.session.execute(stmt)
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "errors_sql": e._sql_message()
            }


    @ns_cart.response(HTTPStatus.OK.value,"Salva os dados de produtos no carrinho de compras")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Falha ao salvar registro!")
    @auth.login_required
    def post(self):
        try:

            itens = request.get_json()

            for item in itens:
                pItem = db.session.execute(Select(B2bCartShopping).where(and_(
                    B2bCartShopping.id_customer==int(item['id_customer']),
                    B2bCartShopping.id_product==int(item['id_product']),
                    B2bCartShopping.color==item['color'],
                    B2bCartShopping.size==item['size']
                ))).scalar()
                if pItem is None:
                    it = B2bCartShopping()
                    it.id_customer = int(item['id_customer'])
                    it.id_product  = int(item['id_product'])
                    it.color       = item['color']
                    it.size        = item['size']
                    it.price       = item['price']
                    it.quantity    = int(item['quantity'])
                    db.session.add(it)
                    db.session.commit()
                else:
                    pItem.price = item['price']
                    pItem.quantity = int(item['quantity'])
                    db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "errors_sql": e._sql_message()
            }
        

@ns_cart.route("/<int:id_product>")
@ns_cart.param("id_product","Id do produto")
class CartItem(Resource):
    @auth.login_required
    def get(self,id_product:int):
        id_customer = int(request.args.get("id_profile"))
        cquery = Select(B2bCartShopping.color).distinct()\
            .where(and_(B2bCartShopping.id_customer==id_customer,B2bCartShopping.id_product==id_product))
        
        squery = Select(B2bCartShopping.size,B2bCartShopping.quantity).distinct()\
            .where(and_(B2bCartShopping.id_product==id_product,B2bCartShopping.id_customer==id_customer))

        return {
            "id_product": id_product,
            "ref": "",
            "name": "",
            "img_url": "",
            "price_un": "",
            "total_price": "",
            "itens":0,
            "colors":[{
                "name": "",
                "hexa": "",
                "code": c.color,
                "sizes": [{
                    "name": s.size,
                    "quantity": s.quantity
                }for s in db.session.execute(squery.where(B2bCartShopping.color==c.color)).all()]
            }for c in db.session.execute(cquery).all()]
        }


@ns_cart.param('id_entity','Código do perfil',"query",type=int)
class CartTotal(Resource):
    @auth.login_required
    @ns_cart.response(HTTPStatus.OK.value,"Lista o total de produtos no carrinho")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Falha ao contar registros!")
    def get(self,id_entity:int):
        query = Select(func.count(distinct(tuple_(B2bCartShopping.id_product))).label("total"))\
            .select_from(B2bCartShopping)\
            .where(B2bCartShopping.id_customer==id_entity)
        return db.session.execute(query).one().total

ns_cart.add_resource(CartTotal,'/total/<int:id_entity>')
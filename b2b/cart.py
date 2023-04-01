
from decimal import Decimal
from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bCartShopping, CmmProducts, CmmTranslateColors, CmmTranslateSizes,CmmProductsImages, db
from sqlalchemy import exc,Select,and_,func,tuple_,distinct,desc,asc
import json
from auth import auth

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
            rquery = Select(B2bCartShopping.id_product,
                            B2bCartShopping.color.label("color_code"),
                            B2bCartShopping.size.label("size_code"),
                            B2bCartShopping.quantity,
                            B2bCartShopping.price,
                            CmmProducts.name,
                            CmmProducts.refCode,
                            CmmTranslateColors.hexcode.label("color_hexa"),
                            CmmTranslateSizes.size_name)\
                .join(CmmProducts,CmmProducts.id==B2bCartShopping.id_product)\
                .join(CmmTranslateColors,CmmTranslateColors.color==B2bCartShopping.color)\
                .join(CmmTranslateSizes,CmmTranslateSizes.size==B2bCartShopping.size)\
                .join(CmmProductsImages,and_(CmmProductsImages.id_product==CmmProducts.id,CmmProductsImages.img_default==True))\
                .where(B2bCartShopping.id_customer==id_profile)\
                .order_by(direction(getattr(B2bCartShopping, order_by)))

            return [{
                        "id": p.id_product,
                        "ref": p.refCode,
                        "name": p.name,
                        "color_code": p.color_code,
                        "size_code": p.size_code,
                        "quantity": p.quantity,
                        "price": str(p.price),
                        "color_hexa": p.color_hexa,
                        "size_name" : p.size_name
                    } for p in db.session.execute(rquery).all()]
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }


    @ns_cart.response(HTTPStatus.OK.value,"Salva os dados de produtos no carrinho de compras")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Falha ao salvar registro!")
    @ns_cart.param("id_customer","Código do Cliente","formData",type=int,required=True)
    @ns_cart.param("id_product","Código do produto","formData",type=int,required=True)
    @ns_cart.param("color","Código da cor","formData",required=True)
    @ns_cart.param("size","Código do tamanho","formData",required=True)
    @ns_cart.param("quantity","Quantidade desejada","formData",required=True)
    @ns_cart.param("price","Preço do produto","formData",required=True)
    @auth.login_required
    def post(self):
        try:
            pItem = db.session.execute(Select(B2bCartShopping).where(and_(
                B2bCartShopping.id_customer==int(request.form.get("id_customer")),
                B2bCartShopping.id_product==int(request.form.get("id_product")),
                B2bCartShopping.color==request.form.get("color"),
                B2bCartShopping.size==request.form.get("size")
            ))).one()

            db.session.delete(pItem)
            db.session.commit()
        except:
            pass
        try:
            cart = B2bCartShopping()
            cart.id_customer = int(request.form.get("id_customer"))
            cart.id_product  = int(request.form.get("id_product"))
            cart.color       = request.form.get("color")
            cart.size        = request.form.get("size")
            cart.quantity    = request.form.get("quantity")
            cart.price       = request.form.get("price")

            db.session.add(cart)
            db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "errors_sql": e._sql_message()
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
        print(query)
        return db.session.execute(query).one().total

ns_cart.add_resource(CartTotal,'/total/<int:id_entity>')
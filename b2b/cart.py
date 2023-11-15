
from http import HTTPStatus
from flask_restx import Resource,Namespace,fields
from flask import request
from models import B2bCartShopping, B2bCustomerRepresentative, B2bProductStock, CmmLegalEntities, CmmProducts, CmmProductsGrid, CmmProductsGridDistribution, CmmTranslateColors, CmmTranslateSizes,CmmProductsImages, db
from sqlalchemy import exc,Select,and_,func,tuple_,distinct,desc,asc,Delete, text
from auth import auth
from config import Config

ns_cart = Namespace("cart",description="Operações para manipular dados do carrinho de compras")

m_list_content = ns_cart.model(
    "Content",{
        "customer":fields.Integer,
        "color": fields.Integer,
        "products": fields.List(fields.Integer)
    }
)

@ns_cart.route("/")
class CartApi(Resource):
    @ns_cart.response(HTTPStatus.OK.value,"Retorna os dados de produtos que estão no carrinho de compras")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar registros")
    @ns_cart.param("id_profile","Número da página de registros","query",type=int,required=True,default=1)
    @ns_cart.param("order_by","Campo de ordenacao","query")
    @ns_cart.param("order_dir","Direção da ordenação","query",enum=['ASC','DESC'])
    @auth.login_required
    def get(self):
        id_profile =  int(request.args.get("id_profile"))
        order_by   = "id_product" if request.args.get("order_by") is None else request.args.get("order_by")
        direction  = desc if request.args.get("order_dir") == 'DESC' else asc
        user_type  = request.args.get("userType")

        try:
            
            pquery = Select(B2bCartShopping.id_product,
                            B2bCartShopping.id_customer,
                            CmmLegalEntities.fantasy_name,
                            B2bCartShopping.price,
                            CmmProductsImages.img_url,
                            CmmProducts.name,CmmProducts.refCode,
                            func.sum(B2bCartShopping.quantity).label("total")).distinct()\
                .join(CmmProductsImages,and_(CmmProductsImages.id_product==B2bCartShopping.id_product,CmmProductsImages.img_default==True))\
                .join(CmmLegalEntities,CmmLegalEntities.id==B2bCartShopping.id_customer)\
                .join(CmmProducts,CmmProducts.id==B2bCartShopping.id_product)\
                .group_by(B2bCartShopping.id_product)
            
            #colors query
            cquery = Select(B2bCartShopping.id_color,CmmTranslateColors.hexcode,CmmTranslateColors.name).distinct()\
                .join(CmmTranslateColors,CmmTranslateColors.id==B2bCartShopping.id_color)\
            
            if user_type=='C':
                pquery = pquery.where(B2bCartShopping.id_customer==id_profile).order_by(direction(getattr(B2bCartShopping,order_by)))
            elif user_type=='R':
                pquery = pquery.where(B2bCartShopping.id_customer.in_(
                    Select(B2bCustomerRepresentative.id_customer).where(B2bCustomerRepresentative.id_representative==id_profile)
                )).group_by(B2bCartShopping.id_customer).order_by(asc(B2bCartShopping.id_customer))
            elif user_type=='A':
                pquery = pquery.group_by(B2bCartShopping.id_customer).order_by(asc(B2bCartShopping.id_customer))
            
            return [{
                "id_product": m.id_product,
                "id_customer":m.id_customer,
                "fantasy_name": m.fantasy_name,
                "ref": m.refCode,
                "name": m.name,
                "img_url": m.img_url,
                "price_un": float(str(m.price)),
                "itens": int(str(m.total)),
                "total_price": float(str(m.total*m.price)),
                "colors":[{
                    "name": c.name,
                    "hexa": c.hexcode,
                    "code": c.id_color,
                    "sizes":[{
                        "name": s.new_size,
                        "quantity": int(0 if s.quantity is None else s.quantity)
                    } for s in self.get_sizes(m.id_customer,m.id_product,c.id_color)]
                }for c in db.session.execute(cquery.where(and_(B2bCartShopping.id_customer==m.id_customer,B2bCartShopping.id_product==m.id_product)))]
            } for m in db.session.execute(pquery).all()]

        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }

    def get_sizes(self,id_customer:int,id_product:int,color:str):
        subquery = Select(
            B2bCartShopping.id_size.label("size_code"),
            B2bCartShopping.quantity)\
            .where(and_(B2bCartShopping.id_customer==id_customer,B2bCartShopping.id_product==id_product,B2bCartShopping.id_color==color)).cte()

        return db.session.execute(Select(CmmTranslateSizes.new_size,subquery.c.size_code,subquery.c.quantity).distinct()\
            .outerjoin(subquery,subquery.c.size_code==CmmTranslateSizes.id)).all()

    @ns_cart.response(HTTPStatus.OK.value,"Retorna verdadeiro ou falso se conseguiu excluir o(s) registro(s)")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Falha ao excluir")
    @auth.login_required
    def delete(self):
        try:
            req = request.get_json()
            stmt = Delete(B2bCartShopping).where(
                and_(
                    B2bCartShopping.id_product.in_(req['products']),
                    B2bCartShopping.id_customer==int(req['customer'])
                )
            )
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
                    B2bCartShopping.id_color==item['id_color'],
                    B2bCartShopping.id_size==item['id_size']
                ))).scalar()
                if pItem is None:
                    it = B2bCartShopping()
                    it.id_customer = int(item['id_customer'])
                    it.id_product  = int(item['id_product'])
                    it.id_color    = item['id_color']
                    it.id_size     = item['id_size']
                    it.price       = item['price']
                    it.quantity    = int(item['quantity'])
                    it.user_create = item["user_create"]
                    db.session.add(it)
                    db.session.commit()
                else:
                    pItem.price       = item['price']
                    pItem.quantity    = int(item['quantity'])
                    pItem.user_update = item["user_create"]
                    db.session.commit()
            return True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "errors_sql": e._sql_message()
            }
    
    @ns_cart.response(HTTPStatus.OK.value,"Adição em massa de produtos no carrinho de compras utilizando a configuracao de grade")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Falha ao salvar registro!")
    @ns_cart.doc(body=m_list_content,description="Dados necessários dos produtos",name="content")
    def put(self):
        totalExecuted = 0
        try:
            req = request.get_json()
            
            for product in req['products']:
                #busca primeiramente a grade padrao dos produtos na cor desejada
                #se nao houver dados infelizmente nao restarah nada a ser feito
                gquery = db.session.execute(Select(CmmProductsGridDistribution.id_size,
                                CmmProductsGridDistribution.value,CmmProducts.price)\
                        .join(CmmProductsGrid,CmmProductsGrid.id==CmmProductsGridDistribution.id_grid)\
                        .join(CmmProducts,CmmProducts.id_grid==CmmProductsGrid.id)\
                        .where(and_(
                            CmmProductsGridDistribution.id_color==req['color'],
                            CmmProducts.id==product,
                            CmmProductsGrid.default==True
                        )))

                if gquery is not None:
                    totalExecuted += 1
                    for size in gquery:
                        #realiza a busca da quantidade baseada nas informacoes da grade
                        squery = db.session.execute(Select(B2bProductStock.quantity,B2bProductStock.ilimited,B2bProductStock.in_order).where(and_(
                            B2bProductStock.id_product == product,
                            B2bProductStock.id_color == req['color'],
                            B2bProductStock.id_size == size.id_size
                        ))).first()
                        if squery is not None:
                            if squery.ilimited==True:
                                #faz uma verificacao se o produto ja nao esta no carrinho
                                cquery = db.session.execute(Select(func.count().label("total")).select_from(B2bCartShopping).where(
                                    and_(
                                        B2bCartShopping.id_product==product,
                                        B2bCartShopping.id_color==req['color'],
                                        B2bCartShopping.id_size==size.id_size,
                                        B2bCartShopping.id_customer==req['customer']
                                    )
                                )).first()
                                if cquery.total > 0:
                                    bcs = B2bCartShopping.query.get((
                                        req['customer'],
                                        product,
                                        req['color'],
                                        size.id_size))
                                    #incrementa a quantidade com o que tem na grade
                                    if bcs is not None:
                                        bcs.quantity += size.value
                                        db.session.commit()
                                    else:
                                        bcs.quantity = size.value
                                        db.session.commit()
                                else:
                                    bcs = B2bCartShopping()
                                    bcs.id_product  = product
                                    bcs.id_customer = req['customer']
                                    bcs.id_color    = req['color']
                                    bcs.id_size     = size.id_size
                                    bcs.price       = size.price
                                    bcs.quantity    = size.value
                                    bcs.user_create = req['user']
                                    db.session.add(bcs)
                                    db.session.commit()
                                
                            elif (squery.quantity-squery.in_order) >= size.value: #se a quantidade for maior ou igual ao que estah disponivel
                                #faz uma verificacao se o produto ja nao esta no carrinho
                                cquery = db.session.execute(Select(func.count().label("total")).select_from(B2bCartShopping).where(
                                    and_(
                                        B2bCartShopping.id_product==product,
                                        B2bCartShopping.id_color==req['color'],
                                        B2bCartShopping.id_size==size.id_size,
                                        B2bCartShopping.id_customer==req['customer']
                                    )
                                )).first()
                                if cquery.total > 0:
                                    bcs = B2bCartShopping.query.get((
                                        req['customer'],
                                        product['id'],
                                        req['color'],
                                        size.id_size))
                                    
                                    #incrementa a quantidade com o que tem na grade
                                    bcs.quantity += size.value
                                    bcs.user_update = req["user"]
                                    db.session.commit()
                                else:
                                    bcs = B2bCartShopping()
                                    bcs.id_product  = product
                                    bcs.id_customer = req['customer']
                                    bcs.id_color    = req['color']
                                    bcs.id_size     = size.id_size
                                    bcs.price       = size.price
                                    bcs.quantity    = size.value
                                    bcs.user_create = req["user"]
                                    db.session.add(bcs)
                                    db.session.commit()
            return False if totalExecuted==False else True
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "errors_sql": e._sql_message()
            }


@ns_cart.route("/<int:id>")
@ns_cart.param("id","Id")
class CartItem(Resource):
    @ns_cart.hide
    @ns_cart.response(HTTPStatus.OK.value,"Metodo a ser implementado")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Falha ao salvar registro!")
    @auth.login_required
    def get(self,id:int):
        id_customer = int(request.args.get("id_profile"))
        cquery = Select(CmmTranslateColors.color,B2bCartShopping.id_color).distinct()\
            .join(CmmTranslateColors,CmmTranslateColors.id==B2bCartShopping.id_color)\
            .where(and_(B2bCartShopping.id_customer==id_customer,B2bCartShopping.id_product==id))
        
        squery = Select(CmmTranslateSizes.new_size.label("size"),B2bCartShopping.quantity).distinct()\
            .join(CmmTranslateSizes,CmmTranslateSizes.id==B2bCartShopping.id_size)\
            .where(and_(B2bCartShopping.id_product==id,B2bCartShopping.id_customer==id_customer))

        return {
            "id_product": id,
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
                    "quantity": int(s.quantity)
                }for s in db.session.execute(squery.where(B2bCartShopping.id_color==c.id_color))]
            }for c in db.session.execute(cquery)]
        }

    @ns_cart.response(HTTPStatus.OK.value,"Remove os itens do carrinho de compras")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Falha ao remover registros!")
    @auth.login_required
    def delete(self,id:int):
        try:
            usr_type = request.args.get("userType")
            if usr_type=='A':
                #no caso do administrador apagara pelo usuario de criacao do pedido
                #isso evitarah que apague pedidos de outros usuarios
                stmt = Delete(B2bCartShopping).where(B2bCartShopping.user_create==id)
            elif usr_type=='R':
                #quando representante apagara todos os clientes do representante
                stmt = Delete(B2bCartShopping).where(B2bCartShopping.id_customer.in_(
                    Select(B2bCustomerRepresentative.id_customer).where(B2bCustomerRepresentative.id_customer==id)
                    )
                )
            else:
                #sendo cliente apagarah somente os proprios pedidos
                stmt = Delete(B2bCartShopping).where(B2bCartShopping.id_customer==id)

            db.session.execute(stmt)
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
    @ns_cart.response(HTTPStatus.OK.value,"Lista o total de produtos no carrinho")
    @ns_cart.response(HTTPStatus.BAD_REQUEST.value,"Falha ao contar registros!")
    @ns_cart.param("userType","Tipo do usuário","query",enum=['A','C','R'])
    @auth.login_required
    def get(self,id_entity:int):

        userType = request.args.get("userType")

        query = Select(func.count(distinct(tuple_(B2bCartShopping.id_product))).label("total"))\
            .select_from(B2bCartShopping)
            
        if userType=='R':
            #aqui precisa buscar todos os os do representante
            query = query.where(B2bCartShopping.id_customer.in_(
                Select(B2bCustomerRepresentative.id_customer).where(B2bCustomerRepresentative.id_representative==id_entity))
            )
        else:
            query = query.where(B2bCartShopping.id_customer==id_entity)

        #zera o SQL se for admin
        if userType=='A':
            query = Select(func.count(
                    text("DISTINCT id_customer,id_product")
                ).label("total"))\
                    .select_from(B2bCartShopping)

        return db.session.execute(query).one().total if userType!='A' else db.session.execute(query).scalar()

ns_cart.add_resource(CartTotal,'/total/<int:id_entity>')
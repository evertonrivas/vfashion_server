from datetime import datetime
from sqlalchemy import Insert, Select, Update, and_, create_engine, distinct, func, tuple_
from models import B2bCollection, B2bOrdersProducts, CmmLegalEntities, CmmProducts, CmmProductsGrid, CmmProductsGridDistribution, FprDevolution, FprDevolutionItem, B2bOrders, ScmFlimvResult
from dotenv import load_dotenv
from os import environ,path
from sysconfig import LegalEntityType, OrderStatus

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

class Flimv():
    dbconn = None
    internal_flimv = []

    def __init__(self) -> None:
        self.dbconn = create_engine(environ.get("F2B_DB_LIB")+"://"+environ.get("F2B_DB_USER")+":"+environ.get("F2B_DB_PASS")+"@"+environ.get("F2B_DB_HOST")+"/"+environ.get("F2B_DB_NAME"))
        super().__init__()

    def process(self) -> None:
        self.__make_data()
        self.__get_mix()
        self.__get_volume()

    def __make_data(self) -> None:
        with self.dbconn.connect() as conn:
            # realiza a busca de todas as colecoes existentes
            for collection in conn.execute(Select(B2bCollection.id).where(B2bCollection.trash==False)):

                # utilizado para calcular o volume do mix comprado
                total_mix = conn.execute(Select(func.count(CmmProducts.id).label("total")).where(and_(CmmProducts.id_collection==collection.id,CmmProducts.trash==False))).first().total

                # busca todos os clientes existentes
                for cst in conn.execute(Select(CmmLegalEntities.id).where(CmmLegalEntities.type==LegalEntityType.CUSTOMER.value)):
                    
                    ###############################################################
                    #                           FREQUENCY                         #
                    ###############################################################
                    # para o cliente existente, verifica se comprou na colecao (o pedido tem que estar como finalizado)
                    # monta o indicador frequency
                    customer_in_collection = conn.execute(Select(func.count(B2bOrders.id_customer).label("total")).where(
                        B2bOrders.id.in_(
                            Select(B2bOrdersProducts.id_order)\
                            .join(CmmProducts,CmmProducts.id==B2bOrdersProducts.id_product)\
                            .join(B2bCollection,B2bCollection.id==CmmProducts.id_collection)\
                            .where(B2bCollection.id==collection.id)
                        )
                    ).where(and_(
                        B2bOrders.id_customer==cst.id,
                        B2bOrders.status==OrderStatus.FINISHED
                    ))).first().total

                    if customer_in_collection > 0:
                        self.internal_flimv.append({
                            "id_customer": cst.id,
                            "id_collection": collection.id,
                            "frequency": True,
                            "liquidity": 0,
                            "injury": 0,
                            "mix": 0,
                            "volume": 0
                        })

                    ###############################################################
                    #                           INJURY                            #
                    ###############################################################
                    # monta o indicador de injury buscando o total de reclamacoes
                    # isso indiferente se foi aprovada ou nao, o importante eh se o 
                    # cliente abriu devolucao
                    sql_reclamacao_cliente = Select(func.count(FprDevolutionItem.id_product).label("total")).select_from(FprDevolution)\
                    .join(B2bOrders,B2bOrders.id==FprDevolution.id_order)\
                    .join(FprDevolutionItem,FprDevolutionItem.id_devolution==FprDevolution.id)\
                    .join(CmmProducts,CmmProducts.id==FprDevolutionItem.id_product)\
                    .join(CmmProductsGrid,CmmProductsGrid.id==CmmProducts.id_grid)\
                    .join(CmmProductsGridDistribution,CmmProductsGridDistribution.id_grid==CmmProductsGrid.id)\
                    .join(B2bCollection,B2bCollection.id_brand==CmmProducts.id_collection)\
                    .where(and_(
                        B2bCollection.id==collection.id,
                        B2bOrders.id_customer==cst.id,
                        FprDevolutionItem.id_color==CmmProductsGridDistribution.id_color,
                        FprDevolutionItem.id_size==CmmProductsGridDistribution.id_size
                    ))

                    reclamacao_cliente = conn.execute(sql_reclamacao_cliente).first().total

                    if reclamacao_cliente > 0:
                        for flimv in self.internal_flimv:
                            if flimv["id_customer"]==cst.id and flimv["id_collection"]==collection.id:
                                flimv["injury"] = reclamacao_cliente


                    ###############################################################
                    #                              MIX                            #
                    ###############################################################
                    total_aquisition = conn.execute(Select(
                        func.count(distinct(tuple_(B2bOrdersProducts.id_product))).label("total")
                    ).select_from(B2bOrders)\
                    .join(B2bOrdersProducts,B2bOrdersProducts.id_order==B2bOrders.id)\
                    .join(CmmProducts,CmmProducts.id==B2bOrdersProducts.id_product)\
                    .where(
                        and_(
                            B2bOrders.id_customer==cst.id,
                            CmmProducts.id_collection==collection.id
                        )
                    )).first().total
                    if total_aquisition > 0:
                        for flimv in self.internal_flimv:
                            if flimv["id_customer"]==cst.id and flimv["id_collection"]==collection.id:
                                flimv["mix"] = total_mix/total_aquisition
                    

                    ###############################################################
                    #                            VOLUME                           #
                    ###############################################################

    def __get_volume(self) -> None:
        pass

    def __save_flimv(self) -> None:
        with self.dbconn.connect() as conn:
            for flimv in self.internal_flimv:
                # realizar verificacao se ja existe o registro
                exist = conn.execute(Select(ScmFlimvResult.id).where(and_(ScmFlimvResult.id_customer==flimv.id_customer,ScmFlimvResult.id_collection==flimv.id_collection))).first()

                if exist is not None:
                    Update(ScmFlimvResult).values(
                        frequency=flimv.frequency,
                        liquidity=flimv.liquidity,
                        injury=flimv.injury,
                        mix=flimv.mix,
                        volume=flimv.volume,
                    ).where(and_(ScmFlimvResult.id_customer==flimv.id_customer,ScmFlimvResult.id_collection==flimv.id_collection))
                else:
                    conn.execute(
                        Insert(ScmFlimvResult).values(
                            id_customer=flimv.id_customer,
                            id_collection=flimv.id_collection,
                            frequency=flimv.frequency,
                            liquidity=flimv.liquidity,
                            injury=flimv.injury,
                            mix=flimv.mix,
                            volume=flimv.volume,
                            date_ref=datetime.now()
                        )
                    )

            conn.commit()
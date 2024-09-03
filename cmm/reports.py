import base64
import datetime
import decimal
from http import HTTPStatus
import json
import os
from flask_restx import Resource,Namespace,fields
from flask import request
from models import CmmCities, CmmLegalEntities, CmmLegalEntityHistory, CmmReport, CmmStateRegions, CrmFunnel, CrmFunnelStage, CrmFunnelStageCustomer, ScmEvent, _get_params, _show_query,db
from common import _format_action, _gen_report
from sqlalchemy import Select, text, alias, and_, desc, exc, asc, func, or_
from auth import auth
from f2bconfig import Reports
from os import environ

ns_report = Namespace("reports",description="Operações para manipular dados de relatórios")

@ns_report.route("/")
class ReportsApi(Resource):
    @ns_report.response(HTTPStatus.OK.value,"Lista os relatórios existentes no sistema")
    @ns_report.response(HTTPStatus.BAD_REQUEST.value,"Falha ao listar relatórios")
    @ns_report.param("page","Número da página de registros","query",type=int,required=True,default=1)
    @ns_report.param("pageSize","Número de registros por página","query",type=int,required=True,default=25)
    @ns_report.param("query","Texto para busca","query")
    @auth.login_required
    def get(self):
        pag_num  = 1 if request.args.get("page") is None else int(request.args.get("page"))
        pag_size = int(environ.get("F2B_PAGINATION_SIZE")) if request.args.get("pageSize") is None else int(request.args.get("pageSize"))
        query    = "" if request.args.get("query") is None else request.args.get("query")

        try:
            params = _get_params(query)
            direction = asc if hasattr(params,'order')==False else asc if str(params.order).upper()=='ASC' else desc
            order_by  = 'id' if hasattr(params,'order_by')==False else params.order_by
            search    = None if hasattr(params,"search")==False else params.search
            trash     = False if hasattr(params,'trash')==False else True
            list_all  = False if hasattr(params,'list_all')==False else True

            filter_cat = None if hasattr(params,"category")==False else int(params.category)

            rquery = Select(CmmReport.id,
                            CmmReport.name,
                            CmmReport.filters,
                            ).where(CmmReport.trash==trash)\
                            .order_by(direction(getattr(CmmReport,order_by)))
            
            if filter_cat is not None:
                rquery = rquery.where(CmmReport.category==filter_cat)
            
            if search is not None:
                rquery = rquery.where(
                    or_(
                        CmmReport.name.like("%{}%".format(search)),
                        CmmReport.title.like("%{}%".format(search))
                    )
                )
                            
            if list_all==False:
                pag = db.paginate(rquery,page=pag_num,per_page=pag_size)
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
                        "id": r.id,
                        "name": r.name,
                        "filters": str(r.filters).split(","),
                    }for r in db.session.execute(rquery)]
                }
            else:    
                return [{
                    "id": r.id,
                    "name": r.name,
                    "filters": str(r.filters).split(",")
                }for r in db.session.execute(rquery)]
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }



    @ns_report.response(HTTPStatus.OK.value,"Monta um relatório existente no sistema")
    @ns_report.response(HTTPStatus.BAD_REQUEST.value,"Falha ao montar o relatório!")
    @auth.login_required
    def post(self):
        try:
            req = request.get_json()

            cities        = []
            state_regions = []
            countries     = []
            funnels       = []
            categories    = []
            entities      = []
            models        = []
            types         = []
            status_devol  = []
            status_order  = []
            date_start    = None
            date_end      = None

            report:CmmReport = CmmReport.query.get(req["report"])
            for param in req["params"]:
                if "id_cities" in param and len(param["id_cities"]) > 0:               cities        = param["id_cities"]
                if "id_state_regions" in param and len(param["id_state_regions"]) > 0: state_regions = param["id_state_regions"]
                if "id_countries" in param and len(param["id_countries"]) > 0:         countries     = param["id_countries"]
                if "id_funnels" in param and param["id_funnels"] != 0:                 funnels       = param["id_funnels"]
                if "id_categories" in param and len(param["id_categories"]) > 0:       categories    = param["id_categories"]
                if "id_entities" in param and len(param["id_entities"]) > 0:           entities      = param["id_entities"]
                if "id_models" in param and len(param["id_models"]) > 0:               models        = param["id_models"]
                if "id_types" in param and len(param["id_types"]) > 0:                 types         = param["id_types"]
                if "id_status_devol" in param and len(param["id_status_devol"]) > 0:   status_devol  = param["id_status_devol"]
                if "id_status_order" in param and len(param["id_status_order"]) > 0:   status_order  = param["id_status_order"]
                if "date_start" in param: 
                    date_start = param["date_start"]
                    date_end = param["date_end"]


            #montagem da query master
            mqry = report.master_query
            mwhere = str(report.master_where)
            if len(cities) > 0 or len(state_regions) > 0 or len(countries) > 0:
                if len(cities) > 0:
                    mwhere = mwhere.replace("%1",",".join(str(city) for city in cities)).replace("%2","0").replace("%3","0")
                elif len(state_regions) > 0:
                    mwhere = mwhere.replace("%1","0").replace("%2",",".join( str(state) for state in state_regions )).replace("%3","0")
                elif len(countries) > 0:
                    mwhere = mwhere.replace("%1","0").replace("%2","0").replace("%3",",".join( str(country) for country in countries ))

            if len(funnels) > 0:    mwhere = mwhere.replace("%1",",".join(funnels))
            if len(categories) > 0: mwhere = mwhere.replace("%1",",".join(categories))
            if len(entities) > 0:   mwhere = mwhere.replace("%1",",".join(entities))
            if len(models) > 0:     mwhere = mwhere.replace("%1",",".join(models))
            if len(types) > 0:      mwhere = mwhere.replace("%1",",".join(types))
            if len(status_devol)>0: mwhere = mwhere.replace("%1",",".join(status_devol))
            if len(status_order)>0: mwhere = mwhere.replace("%1",",".join(status_order))
            if date_start is not None and date_end is not None: mwhere = str(mwhere).replace("%1","'"+date_start+"'").replace("%2","'"+date_end+"'")

            if mwhere.find("%")>-1:
                mwhere = ""
            mqry += " "+mwhere

            body = []
            mstr = ""
            for data_master in db.session.execute(text(mqry)):
                row = []
                i = 0
                for field_master in str(report.master_fields).split(","):
                    master_type = type(data_master[i])
                    if master_type is datetime.date:
                        row.append("\""+field_master+"\" : \""+data_master[i].strftime("%d/%m/%Y")+"\"")
                    elif master_type is int:
                        row.append("\""+field_master+"\" : \""+str(data_master[i])+"\"")
                    elif master_type is float:
                        row.append("\""+field_master+"\" : \""+str(data_master[i])+"\"")
                    elif master_type is decimal.Decimal:
                        row.append("\""+field_master+"\" : \""+str(data_master[i]).replace(".",",")+"\"")
                    else:
                        row.append("\""+field_master+"\" : \""+("" if data_master[i] is None else data_master[i])+"\"")

                    if report.child_query is not None:
                        if field_master=="id":
                            crow = self.__mount_child(report,data_master[i])
                            row.append("\"child\" : ["+",".join(crow)+"]")

                    i += 1
                mstr = "{"+",".join(row)+"}"
                nrow = eval(mstr)
                body.append(nrow)

            if _gen_report(
                report.file_model,
                {
                    "title": report.title,
                    "body": body,
                    "footer": ""
                }
            )==False:
                return False
            
            with open(environ.get("F2B_APP_PATH")+'assets/pdf/'+str(report.file_model).replace(".html","")+".pdf","rb") as pdf:
                content = base64.b64encode(pdf.read()).decode("utf-8")
                pdf.close()
                return {
                    "name": str(report.file_model).replace(".html","")+".pdf",
                    "type": "application/pdf",
                    "size": os.path.getsize(environ.get("F2B_APP_PATH")+"assets/pdf/"+str(report.file_model).replace(".html","")+".pdf"),
                    "content": content,
                }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
        
    def __mount_child(self,report:CmmReport,id:int):
        cqry = report.child_query+" "+str(report.child_where).replace("%1",str(id))
        crow = []
        for data_child in db.session.execute(text(cqry)):
            cdata = []
            c = 0
            for field_child in str(report.child_fileds).split(","):
                child_type = type(data_child[c])
                if child_type is datetime.date:
                    cdata.append("\""+field_child+"\" : \""+data_child[c].strftime("%d/%m/%Y")+"\"")
                elif child_type is datetime.datetime:
                    cdata.append("\""+field_child+"\" : \""+data_child[c].strftime("%d/%m/%Y %H:%M")+"\"")
                elif child_type is int:
                    cdata.append("\""+field_child+"\" : \""+str(data_child[c])+"\"")
                elif child_type is float:
                    cdata.append("\""+field_child+"\" : \""+str(data_child[c])+"\"")
                elif child_type is decimal.Decimal:
                    cdata.append("\""+field_child+"\" : \""+str(data_child[c]).replace(".",",")+"\"")
                else:
                    if field_child=="action":
                        cdata.append("\""+field_child+"\" : \""+_format_action(data_child[c])+"\"")
                    else:
                        cdata.append("\""+field_child+"\" : \""+("" if data_child[c] is None else data_child[c])+"\"")

                if report.last_query is not None:
                        if field_child=="id":
                            lrow = self.__mount_last(report,data_child[c])
                            cdata.append("\"last\" : ["+",".join(lrow)+"]")
        
                c += 1
            crow.append("{"+",".join(cdata)+"}")
        return crow
    
    def __mount_last(self,report:CmmReport,id:int):
        lqry = report.last_query+" "+str(report.last_where).replace("%1",str(id))
        lrow = []
        for data_last in db.session.execute(text(lqry)):
            ldata = []
            l = 0
            for field_last in str(report.last_fileds).split(","):
                last_type = type(data_last[l])
                if last_type is datetime.date:
                    ldata.append("\""+field_last+"\" : \""+data_last[l].strftime("%d/%m/%Y")+"\"")
                elif last_type is datetime.datetime:
                    ldata.append("\""+field_last+"\" : \""+data_last[l].strftime("%d/%m/%Y %H:%M")+"\"")
                elif last_type is int:
                    ldata.append("\""+field_last+"\" : \""+str(data_last[l])+"\"")
                elif last_type is float:
                    ldata.append("\""+field_last+"\" : \""+str(data_last[l])+"\"")
                elif last_type is decimal.Decimal:
                    ldata.append("\""+field_last+"\" : \""+str(data_last[l]).replace(".",",")+"\"")
                else:
                    if field_last=="action":
                        ldata.append("\""+field_last+"\" : \""+_format_action(data_last[l])+"\"")
                    else:
                        ldata.append("\""+field_last+"\" : \""+("" if data_last[l] is None else data_last[l])+"\"")
        
                l += 1
            lrow.append("{"+",".join(ldata)+"}")
        return lrow

@ns_report.route("/<int:id>")
class ReporApi(Resource):
    def get(self,id:int):
        try:
            report = CmmReport.query.get(id)
            return {
                "id": report.id,
                "name": report.name,
                "filters": (report.filters).split(",")
            }
        except exc.SQLAlchemyError as e:
            return {
                "error_code": e.code,
                "error_details": e._message(),
                "error_sql": e._sql_message()
            }
from flask import Flask
from flask_cors import CORS
from sfm.api import blueprint as sfm
from pdv.api import blueprint as pdv
from crm.api import blueprint as crm
from b2b.api import blueprint as b2b

app = Flask(__name__)

app.register_blueprint(sfm)
app.register_blueprint(pdv)
app.register_blueprint(crm)
app.register_blueprint(b2b)

CORS(app)

@app.route("/")
def index():
    return """Para acessar as documenta&ccedil;&otilde;es das APIS, clique nos links abaixo:<br/><br/>
    VF_SFM - Gestão de For&ccedil;a de Vendas <a href='/sfm/api/v1/'>/sfm/api/v1/</a><br/>
    VF_B2B - Business to Business <a href='/b2b/api/v1'>/b2b/api/v1</a><br/>
    VF_PDV - Ponto de Venda <a href='/pdv/api/v1'>/pdv/api/v1</a><br/>
    VF_CRM - Customer Relashionship Management <a href='/crm/api/v1'>/crm/api/v1</a>
    """


if __name__=="__main__":
    app.run(port=5000,debug=True)
from flask import Flask
from flask_cors import CORS
from cmm.api import blueprint as cmm
from sfm.api import blueprint as sfm
from pdv.api import blueprint as pdv
from crm.api import blueprint as crm
from b2b.api import blueprint as b2b

app = Flask(__name__)

app.register_blueprint(cmm)
app.register_blueprint(sfm)
app.register_blueprint(pdv)
app.register_blueprint(crm)
app.register_blueprint(b2b)

CORS(app)

@app.route("/")
def index():
    return """<html>
        <head>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-GLhlTQ8iRABdZLl6O3oVMWSktQOp6b7In1Zl3/Jr59b6EGGoI1aFkw7cmDA6j6gD" crossorigin="anonymous">
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js" integrity="sha384-w76AqPfDkMBDXo30jS1Sgez6pr3x5MlQ1ZAGC+nuZB+EYdgRZgiwxhTBTkF7CXvN" crossorigin="anonymous"></script>
        </head>
        <body>
        <div class='container'>
            <div class='row'><div class='col'>&nbsp;</div></div>
            <div class='row'><div class='col'>&nbsp;</div></div>
            <div class='row'><div class='col'>&nbsp;</div></div>
            <div class='row'>
                <div class='col-2'>&nbsp;</div>
                <div class='col'>
                    <div class='card border border-info'>
                        <div class='card-header text-center'>Venda Fashion - API</div>
                        <div class='card-body'>
                            <p class='card-text'>
                            O sistema Venda Fashion possui 4 m&oacute;dulos, cada um com seu backend em REST API com sua respectiva documenta&ccedil;&atilde;o.
                            Para acessar as documenta&ccedil;&otilde;es das APIS, clique nos links abaixo:<br/><br/>
                            VF_SFM - Gestão de For&ccedil;a de Vendas <a href='/sfm/api/v1/'>/sfm/api/v1/</a><br/>
                            VF_B2B - Business to Business <a href='/b2b/api/v1'>/b2b/api/v1</a><br/>
                            VF_PDV - Ponto de Venda <a href='/pdv/api/v1'>/pdv/api/v1</a><br/>
                            VF_CRM - Customer Relashionship Management <a href='/crm/api/v1'>/crm/api/v1</a><hr size='1'>

                            VF_CMM - M&oacute;dulo Common (Fun&ccedil;&otilde;es comuns dos m&oacute;dulos) <a href='/cmm/api/v1'>/cmm/api/v1</a>
                            </p>
                        </div>
                    </div>
                </div>
                <div class='col-2'>&nbsp;</div>
            </div>
        </div>
        </body>
        </html>
    """

if __name__=="__main__":
    app.run(port=5000,debug=True)
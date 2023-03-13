from flask import Flask
from flask_cors import CORS
from cmm.api import blueprint as cmm
from pos.api import blueprint as pos
from crm.api import blueprint as crm
from b2b.api import blueprint as b2b
from fpr.api import blueprint as fpr
from models import db
from flask_migrate import Migrate

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://venda_fashion:vd_fashion@localhost/venda_fashion"

# $env:FLASK_APP="main.py" no powerShell do windows

migrate = Migrate(app,db)

db.init_app(app)
migrate.init_app(app,db)

#with app.app_context():
#    db.create_all()
    

app.register_blueprint(cmm)
app.register_blueprint(pos)
app.register_blueprint(crm)
app.register_blueprint(b2b)
app.register_blueprint(fpr)

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
                        <div class='card-header text-center fw-bold'>Venda Fashion - API</div>
                        <div class='card-body'>
                            <p class='card-text'>
                            O sistema Venda Fashion possui 4 m&oacute;dulos, cada um com seu backend em REST API com sua respectiva documenta&ccedil;&atilde;o.
                            Para acessar as documenta&ccedil;&otilde;es das APIS, clique nos links abaixo:<br/><br/>
                            VF_B2B - Business to Business <a href='/b2b/api/v1'>/b2b/api/v1</a><br/>
                            VF_FPR - Finished Product Return <a href='/fpr/api/v1'>/fpr/api/v1</a><br/>
                            VF_POS - Point Of Sale <a href='/pos/api/v1'>/pos/api/v1</a><br/>
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
    app.run(port=5000,debug=True,host="192.168.0.17")
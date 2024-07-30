from flask import Flask
from flask_cors import CORS
from sqlalchemy import text
from cmm.api import blueprint as cmm
from crm.api import blueprint as crm
from b2b.api import blueprint as b2b
from fpr.api import blueprint as fpr
from scm.api import blueprint as scm
from mpg.api import blueprint as mpg
from models import db
from flask_migrate import Migrate
import locale
from dotenv import load_dotenv
from os import environ,path

BASEDIR = path.abspath(path.dirname(__file__))
load_dotenv(path.join(BASEDIR, '.env'))

locale.setlocale(locale.LC_TIME,environ.get("F2B_LOCALE"))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("F2B_DB_LIB")+"://"+environ.get("F2B_DB_USER")+":"+\
environ.get("F2B_DB_PASS")+"@"+environ.get("F2B_DB_HOST")+"/"+environ.get("F2B_DB_NAME")
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_recycle': 280,
    'pool_pre_ping': True
}

migrate = Migrate()

db.init_app(app)
try:
    with app.app_context():
        #valida a conexao com o banco de daods
        with db.engine.begin() as conn:
            conn.execute(text("SELECT 1"))
            conn.close()

        #se nao existirem as tabelas tenta crialas
        db.create_all()
except Exception as e:
    print(e)
    print("###################################################")
    print("Por favor, inicialize a instância do Banco de Dados")
    print("###################################################")
    quit()

migrate.init_app(app,db)

app.register_blueprint(cmm)
app.register_blueprint(crm)
app.register_blueprint(b2b)
app.register_blueprint(fpr)
app.register_blueprint(scm)
app.register_blueprint(mpg)

CORS(app, resources={r"/*": {"origins": "https://system.fast2bee.com"}},supports_credentials=True)

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
                        <div class='card-header text-center fw-bold'>Fast2Bee - API</div>
                        <div class='card-body'>
                            <p class='card-text'>
                            O sistema Fast2Bee possui 6 m&oacute;dulos, cada um com seu backend em REST API com sua respectiva documenta&ccedil;&atilde;o.
                            Para acessar as documenta&ccedil;&otilde;es das APIS, clique nos links abaixo:<br/><br/>
                            F2B_B2B - Business to Business <a href='/b2b/api'>/b2b/api</a><br>
                            F2B_FPR - Finished Product Return <a href='/fpr/api'>/fpr/api</a><br>
                            F2B_POS - Point Of Sale <a href='/pos/api'>/pos/api</a><br>
                            F2B_CRM - Customer Relashionship Management <a href='/crm/api'>/crm/api</a><br>
                            F2B_SCM - Sales Calendar Management <a href='/scm/api'>/scm/api</a><br>
                            F2B_MPG - Marketing Plan Generator <a href='/mpg/api'>/mpg/api</a><hr size='1'>

                            F2B_CMM - M&oacute;dulo Common (Fun&ccedil;&otilde;es comuns dos m&oacute;dulos) <a href='/cmm/api'>/cmm/api</a>
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
    app.run(port=5500,debug=True,host="0.0.0.0")
from flask import Flask
from flask_cors import CORS
from flask import Blueprint
from flask_restx import Api
from users import api as ns_user
from representatives import api as ns_reps

app = Flask(__name__)

blueprint = Blueprint("api",__name__,url_prefix="/api/v1")

api = Api(blueprint,
    version="1.0",
    title="API Venda Fashion",
    description="Uma API REST para sistema de vendas",
    contact_email="evertonrivas@gmail.com",
    contact="Venda",
    contact_url="http://www.vendafashion.com")

app.register_blueprint(blueprint)
CORS(app)

api.add_namespace(ns_user)
api.add_namespace(ns_reps)







@app.route("/")
def index():
    return "Hello world!"


if __name__=="__main__":
    app.run(port=5000,debug=True)
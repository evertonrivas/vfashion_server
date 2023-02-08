from flask import Flask
from flask_cors import CORS
from api import blueprint

app = Flask(__name__)
app.register_blueprint(blueprint)
CORS(app)

@app.route("/")
def index():
    return "Hello world!"


if __name__=="__main__":
    app.run(port=5000,debug=True)
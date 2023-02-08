from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/',methods=['GET','POST'])
def home():
    return "hello world!"

@app.route('/login',methods=['POST'])
def login(_username:str,_password:str)->str:
    """Funcao que trata o acesso ao sistema e retorna um token

    Args:
        _username (str): login de conexao
        _password (str): senha de conexao

    Returns:
        str: token ou excessao de metodo nao permitido
    """
    return None

@app.route('/config',methods=['POST'])
def config(_configdata:str,_configvalue:str)->bool:
    """Funcao que trata das configuracoes do sistema e retorna verdadeiro ou falso

    Args:
        _configdata (str): _description_
        _configvalue (str): _description_

    Returns:
        str: _description_
    """
    return None

if __name__=="__main__":
    app.run(port=5000)
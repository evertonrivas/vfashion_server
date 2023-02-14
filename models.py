from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


""""id":1,
"username": "teste",
"password": "bolinha",
"name": "Jose",
"type": "A"""""

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name     = db.Column(db.String(255), nullable=False)
    type     = db.Column(db.CHAR,nullable=False)
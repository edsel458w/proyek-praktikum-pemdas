from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organik = db.Column(db.Integer)
    anorganik = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.now())   




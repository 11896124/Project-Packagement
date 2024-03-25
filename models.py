from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Order(db.Model):
    __tablename__ = "Orders"
    order_number = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    order_name = db.Column(db.String, nullable=True)
    order_number_for_user = db.Column(db.Integer, nullable=False)
    order_user_id = db.Column(db.Integer, nullable=False)
    postal_service = db.Column(db.String, nullable=True)
    postal_code = db.Column(db.String, nullable=True)
    barcode = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=False)
    date_arrival = db.Column(db.String, nullable=True)
    date_created = db.Column(db.String, nullable=False)


class User(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    username = db.Column(db.String)
    password = db.Column(db.String)
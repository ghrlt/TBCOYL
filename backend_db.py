from __main__ import app, request, session, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

db_name = "global_db.db"

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# this variable, db, will be used for all SQLAlchemy commands
db = SQLAlchemy(app)



class User(db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
	email = db.Column(db.String, nullable=False)
	password = db.Column(db.String, nullable=False)
	created = db.Column(db.DateTime)

class Link(db.Model):
	__tablename__ = "links"
	id = db.Column(db.Integer, primary_key=True, unique=True)
	owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	owner = db.relationship("User", backref="links.owner_id")

	source_link = db.Column(db.String, nullable=False)
	code = db.Column(db.String, unique=True, nullable=False)

class LinkData(db.Model):
	__tablename__ = "links_data"
	id = db.Column(db.String, db.ForeignKey('links.code'), primary_key=True, unique=True, nullable=False)
	link = db.relationship("Link", backref="links_data.code")

	ad = db.Column(db.Integer, nullable=False)
	views = db.Column(db.Integer, nullable=False)
	expire = db.Column(db.DateTime)





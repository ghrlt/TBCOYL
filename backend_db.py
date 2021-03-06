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
	name = db.Column(db.String, nullable=False)
	email = db.Column(db.String, nullable=False)
	password = db.Column(db.String, nullable=False)
	is_admin = db.Column(db.Boolean, nullable=False)
	created = db.Column(db.DateTime)
	status = db.Column(db.Integer)

	def __init__(self, name, email, password, is_admin, created, status):
		self.name = name
		self.email = email
		self.password = password
		self.is_admin = is_admin
		self.created = created
		self.status = status


class Link(db.Model):
	__tablename__ = "links"
	id = db.Column(db.Integer, primary_key=True, unique=True)
	status = db.Column(db.Integer, nullable=False)
	owner = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	owner_ = db.relationship("User", backref="links.owner")

	source_link = db.Column(db.String, nullable=False)
	code = db.Column(db.String, unique=True, nullable=False)
	domain = db.Column(db.String, nullable=False)

	def __init__(self, status, owner, source_link, code, domain):
		self.status = status
		self.owner = owner
		self.source_link = source_link
		self.code = code
		self.domain = domain


class LinkData(db.Model):
	__tablename__ = "links_data"
	id = db.Column(db.String, primary_key=True, unique=True, nullable=False)
	#id = db.Column(db.String, db.ForeignKey('links.code'), primary_key=True, unique=True, nullable=False)
	#link = db.relationship("Link", backref="links_data.id")

	ad = db.Column(db.Integer, nullable=False)
	views = db.Column(db.Integer, nullable=False)
	created = db.Column(db.DateTime, nullable=False)
	expire = db.Column(db.DateTime)

	def __init__(self, id, link, ad, views, created, expire):
		self.id = id
		self.link = link
		self.ad = ad
		self.views = views
		self.created = created
		self.expire = expire


class UserRevenues(db.Model):
	__tablename__ = "users_revenues"
	id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True, unique=True, nullable=False)
	id_ = db.relationship("User", backref="users_revenues.id")
	revenues = db.Column(db.Integer, nullable=False)

	def __init__(self, id, revenues):
		self.id = id
		self.revenues = revenues


class LinkRevenues(db.Model):
	__tablename__ = "links_revenues"
	date = db.Column(db.DateTime, primary_key=True, nullable=False)
	link = db.Column(db.String, db.ForeignKey('links_data.id'), nullable=False)
	link_ = db.relationship("LinkData", backref="links_revenues.link")
	earned = db.Column(db.Integer, nullable=False)

	def __init__(self, date, link, earned):
		self.date = date
		self.link = link
		self.earned = earned


class Visitor(db.Model):
	__tablename__ = "visitors"
	id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
	visited = db.Column(db.String, db.ForeignKey('links.code'), nullable=False)
	visited_ = db.relationship("Link", backref="visitors.visited")
	visite_date = db.Column(db.DateTime, nullable=False)
	ip = db.Column(db.String, nullable=False)
	referred_from = db.Column(db.String)
	continent = db.Column(db.String)
	country = db.Column(db.String)
	city = db.Column(db.String)
	using_cellular = db.Column(db.Boolean, nullable=False)
	under_proxy = db.Column(db.Boolean, nullable=False)

	def __init__(self, visited, visite_date, ip, referred_from, continent, country, city, using_cellular, under_proxy):
		self.visited = visited
		self.ip = ip
		self.visite_date = visite_date
		self.referred_from = referred_from
		self.continent = continent
		self.country = country
		self.city = city
		self.using_cellular = using_cellular
		self.under_proxy = under_proxy


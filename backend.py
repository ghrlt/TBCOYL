from __main__ import app, request, session, redirect, abort, render_template
from functools import wraps

import backend_db as bdb 

import json
import random
import datetime


def isLoggedIn(f):
	@wraps(f)
	def wrap_isloggedin(*args, **kwargs):
		req_ip = request.remote_addr
		is_logged = True if session.get('loggedin') else False

		if not is_logged:
			return redirect(f"/login?r={request.path}")

		return f(*args, **kwargs)
	return wrap_isloggedin

def isNotLoggedIn(f):
	@wraps(f)
	def wrap_isNotLoggedIn(*args, **kwargs):
		req_ip = request.remote_addr

		if request.args.get('force') != None:
			del session['loggedin']
		
		is_logged = True if session.get('loggedin') else False
		if is_logged:
			r = request.args.get('r')
			return redirect(r or '/')

		return f(*args, **kwargs)
	return wrap_isNotLoggedIn



@app.errorhandler(404)
def handling_links(err):
	link = bdb.Link.query.filter_by(code=request.path.strip('/')).first()
	if link:
		link_data = bdb.LinkData.query.filter_by(id=link.code).first()
		link_data.views += 1

		bdb.db.session.commit()

		if link_data.ad == 1:
			return render_template("ad.html", r_to=link.source_link)

		return redirect( link.source_link )

	return redirect(f"/404?f={request.path}") #Get that from session for better design idk

@app.errorhandler(403)
def handling_403(err):
	return redirect(f"/403?f={request.path}")



@app.route('/login', methods=['POST'])
def loginSys():
	form = request.form
	email = form.get('email')

	u = bdb.User.query.filter_by(email=email).first()
	if not u:
		session['error'] = "Unknown email."
		return redirect("/login")

	if u.password != form.get('password'): # Security lvl 100 - TODO hash
		session['error'] = "Incorrect password entered."
		return redirect("/login")

	try: del session['error']
	except: pass
	session['email'] = email
	session['name'] = u.name
	session['id'] = u.id
	session['loggedin'] = True
	session.permanent = True

	r = form.get('redirect')
	return redirect(r or '/')

@app.route('/register', methods=['POST'])
def registerSys():
	form = request.form
	name = form.get('name')
	email = form.get('email')
	password = form.get('password')

	u = bdb.User.query.filter_by(email=email).first()
	if u:
		session['error'] = "Email already in use, login instead."
		return redirect("/register")

	t = datetime.datetime.utcnow()

	u = bdb.User(name, email, password, t)
	bdb.db.session.add(u)
	bdb.db.session.commit()

	try: del session['error']
	except: pass
	session['email'] = email
	session['name'] = name
	session['id'] = u.id
	session['loggedin'] = True
	session.permanent = True

	r = form.get('redirect')
	return redirect(r or '/dashboard')


@app.route('/create_new_link', methods=['POST'])
def createLinkSys():
	form = request.form
	source = form.get('redirect_to')
	owner = session['id']
	domain = form.get('domain')

	if form.get('expiration'):
		exp_date = datetime.datetime.strptime(form.get('expiration').replace('T', ' '), '%Y-%m-%d %H:%M')
	else:
		exp_date = None

	code = genCode()
	while bdb.Link.query.filter_by(code=code).first():
		code = genCode()

	link = bdb.Link(owner, source, code, domain)
	data = bdb.LinkData(code, source, 1 if form.get('ad') == "true" else 0, 0, exp_date)

	bdb.db.session.add(link)
	bdb.db.session.add(data)
	bdb.db.session.commit()

	return redirect('/dashboard')


#@app.route('/api/load_user_links')
def loadUserLinks():
	user = session['id']
	user = bdb.User.query.filter_by(id=user).first()

	links = bdb.Link.query.filter_by(owner=user.id).all()
	for i, link in enumerate(links):
		link_data = bdb.LinkData.query.filter_by(id=link.code).first()

		links[i].views = link_data.views
		links[i].ad = link_data.ad
		links[i].expires = link_data.expire
		links[i].fullurl = f"{link.domain}/{link.code}"

	return links






def genCode():
	p1 = [chr(random.randint(48,57)) for _ in range(8)]
	p2 = [chr(random.randint(65,90)) for _ in range(8)]
	p3 = [chr(random.randint(97,122)) for _ in range(8)]

	code = ""
	for i in range(8):
		x = random.randint(1,3)
		code += str( eval(f"p{x}")[random.randint(0,7)] )

	return code




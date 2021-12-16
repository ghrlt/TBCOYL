from __main__ import app, request, session, redirect, abort
from functools import wraps

import backend_db as db

import json


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
	with open('links_db.json', 'r') as f:
		links = json.load(f)

	if request.path in links:
		return redirect( links[request.path]['l'] )

	return redirect(f"/404?f={request.path}") #Get that from this or from session for better design, idk

@app.errorhandler(403)
def handling_403(err):
	return redirect(f"/403?f={request.path}")



@app.route('/login', methods=['POST'])
def loginSys():
	form = request.form
	email = form.get('email')

	u = db.User.query.filter_by(email=email).first()
	if not u:
		session['error'] = "Unknown email."
		return redirect("/login")

	if u.password != form.get('password'): # Security lvl 100 - TODO hash
		session['error'] = "Incorrect password entered."
		return redirect("/login")

	try: del session['error']
	except: pass
	session['email'] = email
	session['loggedin'] = True
	session.permanent = True

	r = form.get('redirect')
	return redirect(r or '/')


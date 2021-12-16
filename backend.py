from __main__ import app, request, session, redirect, abort
from functools import wraps

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
		is_logged = True if session.get('loggedin') else False

		if is_logged:
			return redirect(f"{request.args.get('r')}")

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

	# Do check

	# Login
	session['email'] = form.get('email')
	session['loggedin'] = True
	session.permanent = True

	return redirect(form.get('redirect') or '/')

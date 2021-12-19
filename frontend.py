from __main__ import app, request, session, render_template

import backend

@app.route('/')
def home():
	return render_template("index.html")

@app.route('/login')
@backend.isNotLoggedIn
def login():
	page = render_template("login.html")
	try: del session['error']
	except: pass
	
	return page

@app.route('/register')
@backend.isNotLoggedIn
def register():
	page = render_template("register.html")
	try: del session['error']
	except: pass
	
	return page


@app.route('/dashboard')
@backend.isLoggedIn
def dashboard():
	return render_template("dashboard.html", links=reversed(backend.loadUserLinks()))


@app.route('/404')
def notfound_404():
	return render_template("404.html")

@app.route('/403')
def forbidden_403():
	return render_template("403.html")

from __main__ import app, request, render_template

import backend

@app.route('/')
def home():
	return render_template("index.html")

@app.route('/login')
@backend.isNotLoggedIn
def login():
	return render_template("login.html")

@app.route('/dashboard')
@backend.isLoggedIn
def dashboard():
	return render_template("dashboard.html")


@app.route('/404')
def notfound_404():
	return render_template("404.html")

@app.route('/403')
def forbidden_403():
	return render_template("403.html")

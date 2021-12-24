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
@app.route('/dashboard/')
@backend.isLoggedIn
def dashboard():
	return render_template("dashboard.html", links=reversed(backend.loadUserLinks()))

@app.route('/dashboard/links/<code>')
@backend.isLoggedIn
def dashboard_links(code):
	l = backend.loadLinkByCode(code)
	return render_template("dash_links.html", link=l)


@app.route('/admin')
@app.route('/admin/')
@backend.isLoggedInAsAdmin
def admin():
	return render_template("admin/index.html")

@app.route('/admin/links')
@app.route('/admin/links/')
@backend.isLoggedInAsAdmin
def admin_links():
	l = []
	return render_template("admin/links.html", links=l)

@app.route('/admin/users')
@app.route('/admin/users/')
@backend.isLoggedInAsAdmin
def admin_users():
	u = backend.loadUsersList(full=True)
	return render_template("admin/users.html", users=u)


@app.route('/admin/links/<code>')
@backend.isLoggedInAsAdmin
def admin_link(code):
	l = backend.loadLinkByCode(code)
	return render_template("admin/link.html", link=l)

@app.route('/admin/users/<id>')
@backend.isLoggedInAsAdmin
def admin_user(id):
	u = backend.loadUserById(id)
	return render_template("admin/user.html", user=u)



@app.route('/404')
def notfound_404():
	return render_template("404.html")

@app.route('/403')
def forbidden_403():
	return render_template("403.html")

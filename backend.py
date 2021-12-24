from __main__ import app, request, session, redirect, abort, render_template
from functools import wraps

import backend_db as bdb 

import json
import random
import datetime
import requests


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

def isLoggedInAsAdmin(f):
	@wraps(f)
	def wrap_isLoggedInAsAdmin(*args, **kwargs):
		req_ip = request.remote_addr
		is_logged = True if session.get('loggedin') else False

		if not is_logged:
			return redirect(f"/login?r={request.path}")

		if bdb.User.query.filter_by(email=session['email']).first().is_admin:
			return f(*args, **kwargs)
		return abort(403)

	return wrap_isLoggedInAsAdmin



@app.errorhandler(404)
def handling_links(err):
	path = request.path.strip('/')

	link = bdb.Link.query.filter_by(code=path, status=0).first()
	if link:
		link_data = bdb.LinkData.query.filter_by(id=link.code).first()
		link_data.views += 1

		# Stats
		ip = "86.210.67.40"#request.remote_addr
		ii = requests.get(f"http://ip-api.com/json/{ip}?fields=status,continent,country,city,timezone,isp,mobile,proxy,query").json()
		if ii['status'] == "success":
			visitor = bdb.Visitor(
				link.code, datetime.datetime.utcnow(),
				ip, request.referrer,
				ii['continent'], ii['country'],
				ii['city'], ii['mobile'], ii['proxy']
			)
			bdb.db.session.add(visitor)
		
		bdb.db.session.commit()


		if link_data.ad == 1:
			return render_template("ad.html", r_to=link.source_link)
		return redirect( link.source_link )

	elif bdb.Link.query.filter_by(code=path, status=1).first():
		return redirect(f"/disabled?f={path}")

	return redirect(f"/404?f={request.path}")

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

	if u.status == -1:
		session['error'] = "This account has been banned."
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
	password = form.get('password') # Security lvl 100 - TODO hash

	u = bdb.User.query.filter_by(email=email).first()
	if u:
		session['error'] = "Email already in use, login instead."
		return redirect("/register")

	t = datetime.datetime.utcnow()
	u = bdb.User(name, email, password, False, t, 0)
	bdb.db.session.add(u)
	m = bdb.Monetization(u.id, 0)
	bdb.db.session.add(m)
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

	cre_date = datetime.datetime.now()

	if form.get('expiration'):
		exp_date = datetime.datetime.strptime(form.get('expiration').replace('T', ' '), '%Y-%m-%d %H:%M')
	else:
		exp_date = None

	code = genCode()
	while bdb.Link.query.filter_by(code=code).first():
		code = genCode()

	link = bdb.Link(0, owner, source, code, domain)
	data = bdb.LinkData(code, source, 1 if form.get('ad') == "true" else 0, 0, cre_date, exp_date)

	bdb.db.session.add(link)
	bdb.db.session.add(data)
	bdb.db.session.commit()

	return redirect('/dashboard')



@app.route('/dashboard/links/<code>/disable', methods=['POST'])
def disableLinkByCode(code):
	link = bdb.Link.query.filter_by(code=code).first()
	link.status = 1
	bdb.db.session.commit()

	return redirect(f"/dashboard/links/{code}")

@app.route('/dashboard/links/<code>/enable', methods=['POST'])
def enableLinkByCode(code):
	link = bdb.Link.query.filter_by(code=code).first()
	link.status = 0
	bdb.db.session.commit()

	return redirect(f"/dashboard/links/{code}")

@app.route('/dashboard/links/<code>/delete', methods=['POST'])
def deleteLinkByCode(code):
	link = bdb.Link.query.filter_by(code=code).first()
	link.status = -1
	bdb.db.session.commit()

	return redirect("/dashboard")

@app.route('/admin/links/<code>/ban', methods=['POST'])
@isLoggedInAsAdmin
def banLinkByCode(code):
	link = bdb.Link.query.filter_by(code=code).first()
	link.status = -1
	bdb.db.session.commit()

	return redirect("/admin/links")


@app.route('/admin/users/<id>/ban', methods=['POST'])
@isLoggedInAsAdmin
def banUserByCode(id):
	user = bdb.User.query.filter_by(id=id).first()
	user.status = -1
	bdb.db.session.commit()

	return redirect("/admin/users")


#@app.route('/api/load_user_links')
def loadUserLinks():
	user = session['id']
	user = bdb.User.query.filter_by(id=user).first()

	links = bdb.Link.query.filter_by(owner=user.id).all()
	for i, link in enumerate(links):
		if link.status == -1:
			links.pop(i)
			continue

		link_data = bdb.LinkData.query.filter_by(id=link.code).first()

		links[i].views = link_data.views
		links[i].ad = link_data.ad
		links[i].created = link_data.created
		links[i].expires = link_data.expire
		links[i].fullurl = f"{link.domain}/{link.code}"

	return links

#app.route('/api/load_link')
def loadLinkByCode(code):
	link = bdb.Link.query.filter_by(code=code).first()
	if not link: return None

	l_data = bdb.LinkData.query.filter_by(id=link.code).first()

	link.views = l_data.views
	link.ad = l_data.ad
	link.created = l_data.created
	link.expires = l_data.expire
	link.fullurl = f"{link.domain}/{link.code}"

	link.visitors = bdb.Visitor.query.filter_by(visited=link.code).all()

	# By period stats
	link.n_visitors = {"day": 0, "last_day": 0, "month": 0, "last_month": 0}
	for visitor in link.visitors:
		if visitor.visite_date > datetime.datetime.now()-datetime.timedelta(days=61):
			if visitor.visite_date > datetime.datetime.now()-datetime.timedelta(days=30):
				link.n_visitors['month'] += 1
			else:
				link.n_visitors['last_month'] += 1

			if visitor.visite_date > datetime.datetime.now()-datetime.timedelta(days=2):
				if visitor.visite_date > datetime.datetime.now()-datetime.timedelta(days=1):
					link.n_visitors['day'] += 1
				else:
					link.n_visitors['last_day'] += 1


	# Country stats
	link.visitors_country_list = {}
	country_to_cc = {
		"Bangladesh": "BD",
		"Belgium": "BE",
		"Burkina Faso": "BF",
		"Bulgaria": "BG",
		"Bosnia and Herz.": "BA",
		"Brunei": "BN",
		"Bolivia": "BO",
		"Japan": "JP",
		"Burundi": "BI",
		"Benin": "BJ",
		"Bhutan": "BT",
		"Jamaica": "JM",
		"Botswana": "BW",
		"Brazil": "BR",
		"Bahamas": "BS",
		"Belarus": "BY",
		"Belize": "BZ",
		"Russia": "RU",
		"Rwanda": "RW",
		"Serbia": "RS",
		"Lithuania": "LT",
		"Luxembourg": "LU",
		"Liberia": "LR",
		"Romania": "RO",
		"Guinea-Bissau": "GW",
		"Guatemala": "GT",
		"Greece": "GR",
		"Eq. Guinea": "GQ",
		"Guyana": "GY",
		"Georgia": "GE",
		"United Kingdom": "GB",
		"Gabon": "GA",
		"Guinea": "GN",
		"Gambia": "GM",
		"Greenland": "GL",
		"Kuwait": "KW",
		"Ghana": "GH",
		"Oman": "OM",
		"Somaliland": "_2",
		"Kosovo": "_1",
		"N. Cyprus": "_0",
		"Jordan": "JO",
		"Croatia": "HR",
		"Haiti": "HT",
		"Hungary": "HU",
		"Honduras": "HN",
		"Puerto Rico": "PR",
		"Palestine": "PS",
		"Portugal": "PT",
		"Paraguay": "PY",
		"Panama": "PA",
		"Papua New Guinea": "PG",
		"Peru": "PE",
		"Pakistan": "PK",
		"Philippines": "PH",
		"Poland": "PL",
		"Zambia": "ZM",
		"W. Sahara": "EH",
		"Estonia": "EE",
		"Egypt": "EG",
		"South Africa": "ZA",
		"Ecuador": "EC",
		"Albania": "AL",
		"Angola": "AO",
		"Kazakhstan": "KZ",
		"Ethiopia": "ET",
		"Zimbabwe": "ZW",
		"Spain": "ES",
		"Eritrea": "ER",
		"Montenegro": "ME",
		"Moldova": "MD",
		"Madagascar": "MG",
		"Morocco": "MA",
		"Uzbekistan": "UZ",
		"Myanmar": "MM",
		"Mali": "ML",
		"Mongolia": "MN",
		"Macedonia": "MK",
		"Malawi": "MW",
		"Mauritania": "MR",
		"Uganda": "UG",
		"Malaysia": "MY",
		"Mexico": "MX",
		"Vanuatu": "VU",
		"France": "FR",
		"Finland": "FI",
		"Fiji": "FJ",
		"Falkland Is.": "FK",
		"Nicaragua": "NI",
		"Netherlands": "NL",
		"Norway": "NO",
		"Namibia": "NA",
		"New Caledonia": "NC",
		"Niger": "NE",
		"Nigeria": "NG",
		"New Zealand": "NZ",
		"Nepal": "NP",
		"Côte d'Ivoire": "CI",
		"Switzerland": "CH",
		"Colombia": "CO",
		"China": "CN",
		"Cameroon": "CM",
		"Chile": "CL",
		"Canada": "CA",
		"Congo": "CG",
		"Central African Rep.": "CF",
		"Dem. Rep. Congo": "CD",
		"Czech Rep.": "CZ",
		"Cyprus": "CY",
		"Costa Rica": "CR",
		"Cuba": "CU",
		"Swaziland": "SZ",
		"Syria": "SY",
		"Kyrgyzstan": "KG",
		"Kenya": "KE",
		"S. Sudan": "SS",
		"Suriname": "SR",
		"Cambodia": "KH",
		"El Salvador": "SV",
		"Slovakia": "SK",
		"Korea": "KR",
		"Slovenia": "SI",
		"Dem. Rep. Korea": "KP",
		"Somalia": "SO",
		"Senegal": "SN",
		"Sierra Leone": "SL",
		"Solomon Is.": "SB",
		"Saudi Arabia": "SA",
		"Sweden": "SE",
		"Sudan": "SD",
		"Dominican Rep.": "DO",
		"Djibouti": "DJ",
		"Denmark": "DK",
		"Germany": "DE",
		"Yemen": "YE",
		"Austria": "AT",
		"Algeria": "DZ",
		"United States": "US",
		"Latvia": "LV",
		"Uruguay": "UY",
		"Lebanon": "LB",
		"Lao PDR": "LA",
		"Taiwan": "TW",
		"Trinidad and Tobago": "TT",
		"Turkey": "TR",
		"Sri Lanka": "LK",
		"Tunisia": "TN",
		"Timor-Leste": "TL",
		"Turkmenistan": "TM",
		"Tajikistan": "TJ",
		"Lesotho": "LS",
		"Thailand": "TH",
		"Fr. S. Antarctic Lands": "TF",
		"Togo": "TG",
		"Chad": "TD",
		"Libya": "LY",
		"United Arab Emirates": "AE",
		"Venezuela": "VE",
		"Afghanistan": "AF",
		"Iraq": "IQ",
		"Iceland": "IS",
		"Iran": "IR",
		"Armenia": "AM",
		"Italy": "IT",
		"Vietnam": "VN",
		"Argentina": "AR",
		"Australia": "AU",
		"Israel": "IL",
		"India": "IN",
		"Tanzania": "TZ",
		"Azerbaijan": "AZ",
		"Ireland": "IE",
		"Indonesia": "ID",
		"Ukraine": "UA",
		"Qatar": "QA",
		"Mozambique": "MZ"
	}
	for visitor in link.visitors:
		if not visitor.country in link.visitors_country_list:
			c = Country()
			c.n_visitors = 0
			c.name = visitor.country
			c.code = country_to_cc[c.name]
			link.visitors_country_list[visitor.country] = c

		c = link.visitors_country_list[visitor.country]
		c.n_visitors += 1

	temp = {}
	for country in link.visitors_country_list.values():
		temp[country.name] = country.n_visitors

	total_visitors = sum([n_v for n_v in temp.values()])
	for c,n_v in temp.items():
		link.visitors_country_list[c].prct_visitors = (100*n_v)/total_visitors

	temp1 = link.visitors_country_list
	temp2 = sorted(link.visitors_country_list, key=lambda k: link.visitors_country_list[k].prct_visitors, reverse=True)
	link.visitors_country_list = {}
	for key in temp2:
		link.visitors_country_list[key] = temp1[key]

	del temp
	del temp1
	del temp2


	# Referrer stats
	link.visitors_referrer_list = {}
	for visitor in link.visitors:
		if not visitor.referred_from in link.visitors_referrer_list:
			r = Referrer()
			r.n_visitors = 0
			r.name = visitor.referred_from
			link.visitors_referrer_list[r.name] = r

		r = link.visitors_referrer_list[visitor.referred_from]
		r.n_visitors += 1

	temp = {}
	for country in link.visitors_referrer_list.values():
		temp[country.name] = country.n_visitors

	total_visitors = sum([n_v for n_v in temp.values()])
	for c,n_v in temp.items():
		link.visitors_referrer_list[c].prct_visitors = (100*n_v)/total_visitors

	temp1 = link.visitors_referrer_list
	temp2 = sorted(link.visitors_referrer_list, key=lambda k: link.visitors_referrer_list[k].prct_visitors, reverse=True)
	link.visitors_referrer_list = {}
	for key in temp2:
		link.visitors_referrer_list[key] = temp1[key]

	del temp
	del temp1
	del temp2	
	return link


#@app.route('/api/load_users_list')
def loadUsersList(full=False):
	users = bdb.User.query.all()
	if full:
		for i,user in enumerate(users):
			users[i].links = []
			for link in bdb.Link.query.filter_by(owner=user.id).all():
				link_data = bdb.LinkData.query.filter_by(id=link.code).first()

				link.ad = link_data.ad
				link.views = link_data.views
				link.created = link_data.created
				link.expire = link_data.expire

				link.revenues_data = bdb.LinkRevenues.query.filter_by(link=link.code).all()
				link.revenues_total = sum([l.earned for l in link.revenues_data])


				users[i].links.append(link)
			
			users[i].revenues_total = bdb.UserRevenues.query.filter_by(id=link.owner).first().revenues

	return users

#@app.route('/api/load_user')
def loadUserById(id):
	user = bdb.User.query.filter_by(id=id).first()
	if not user: return None

	u_revenues = bdb.UserRevenues.query.filter_by(id=user.id).first()
	user.revenues_total = u_revenues.revenues

	user.links = bdb.Link.query.filter_by(owner=user.id).all()

	return user



class Country:
	def __init__(self):
		pass

class Referrer:
	def __init__(self):
		pass


def genCode():
	p1 = [chr(random.randint(48,57)) for _ in range(8)]
	p2 = [chr(random.randint(65,90)) for _ in range(8)]
	p3 = [chr(random.randint(97,122)) for _ in range(8)]

	code = ""
	for i in range(8):
		x = random.randint(1,3)
		code += str( eval(f"p{x}")[random.randint(0,7)] )

	return code




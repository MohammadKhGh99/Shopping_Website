import os
import sqlite3
import datetime

import flask_login
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
# from flask_jsglue import JSGlue

from flask import render_template, jsonify, Flask, request, redirect, url_for, flash, session
from database_handling import *

app = Flask(__name__)  # , static_folder="static", template_folder="templates")
app.secret_key = 'lakjfpoek[gf;sldg165478'
app.config['DEBUG'] = True
# jsglue = JSGlue(app)

# app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///Shopping.db'
# db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# books_lst = [filename for filename in os.listdir('static/images/books')] * 4
clothes_lst = [filename for filename in os.listdir('static/images/clothes')] * 4
cities = open("cities.txt", "r", encoding="utf8").readlines()

with open("static/Books_Authors.txt", encoding="utf8") as f:
	authors = f.readlines()
with open("static/Books_Dates.txt", encoding="utf8") as f:
	publishes = f.readlines()
with open("static/Books_Publishers.txt", encoding="utf8") as f:
	publishers = f.readlines()

# with open("static/Books_Others.txt", encoding="utf8") as f:
#     other = f.readlines()


NO_ACCOUNTS = True


class User(UserMixin):
	def __init__(self, id_number, phone_number, first_name, last_name, role, date_joined, city, address, backup_phone, password):
		self.id_number = id_number
		self.phone_number = phone_number
		self.first_name = first_name
		self.last_name = last_name
		self.role = role
		self.date_joined = date_joined
		self.city = city
		self.address = address
		self.backup_phone = backup_phone
		self.password = password
		self.authenticated = False
		self.is_active = True
	
	def is_active(self):
		return self.is_active
	
	def is_anonymous(self):
		return False
	
	def is_authenticated(self):
		return self.authenticated
	
	# def is_active(self):
	# 	return True
	
	def get_id(self):
		return self.id_number


@app.route('/home')
def home():
	customer = True
	if current_user.is_authenticated and current_user.role == "admin":
		customer = False
	return render_template('home.html', customer=customer)


@app.route('/books')
def books():
	customer = True
	if current_user.is_authenticated and current_user.role == "admin":
		customer = False
	with sqlite3.connect("Shopping.db") as connection:
		cursor = connection.cursor()
		try:
			cursor.execute("""
			select * from Products
			""")
			
			all_books = cursor.fetchall()
			connection.commit()
		except Exception as e:
			connection.rollback()
			flash("خطأ في تحميل الكتب", "error")
			return redirect(url_for('books'))
	
	# books_lst = [filename for filename in os.listdir('static/images/books')]
	# books_lst = {folder: [os.listdir(f"static/images/books/{folder}")[0], "كتب"] for folder in books_lst}
	return render_template('books.html', products=all_books, authors=authors, publishes=publishes, publishers=publishers,
	                       customer=customer)  # , other=other)


@login_manager.user_loader
def load_user(user_id):
	with sqlite3.connect("Shopping.db") as connection:
		cursor = connection.cursor()
		check_user_existence = f"""
            select *
            from Customers
            where id_number = '{user_id}'
            """
		result = cursor.execute(check_user_existence).fetchone()
		if result:
			return User(*result)
		else:
			return None


@app.route('/clothes')
def clothes():
	customer = True
	if current_user.is_authenticated and current_user.role == "admin":
		customer = False
	return render_template('clothes.html', products=clothes_lst, customer=customer)


@app.route('/login', methods=['POST', 'GET'])
def login():
	if request.method == 'POST':
		
		phone_number = request.form['customer-phone']
		password = request.form['customer-password']
		
		with sqlite3.connect('Shopping.db') as connection:
			cursor = connection.cursor()
			check_user_existence = f"""
                select *
                from Customers
                where phone_number = '{phone_number}'
                """
			res_rows = cursor.execute(check_user_existence)
			res_rows = res_rows.fetchall()
			# todo - in this time we have just admins
			if res_rows[0][4] != "admin":
				flash("فقط المسؤول يمكنه تسجيل الدخول", "warning")
				return redirect(url_for('home'))
			
			if len(res_rows) == 1:
				if bcrypt.check_password_hash(res_rows[0][-1], password):
					user = load_user(res_rows[0][0])
					# print(user.is_active)
					login_user(user)
					flash("تم تسجيل الدخول بنجاح!", category="success")
					if current_user.role == "admin":
						# print("1232")
						return redirect(url_for('admin_profile'))
					return redirect(url_for('profile'))
			
			# return render_template("logged_in.html")
			else:
				flash("لم تقم بالتسجيل في الموقع من قبل, تفضّل بالتسجيل في الموقع", category="warning")
				return redirect(url_for('register'))
	if current_user.is_authenticated:
		if current_user.role == "admin":
			return redirect(url_for('admin_profile'))
		return redirect(url_for('profile'))
	
	customer = True
	if current_user.is_authenticated and current_user.role == "admin":
		customer = False
	# flash("خطأ في تسجيل الدخول, إحدى الخانات تحتاج للتعديل", category="warning")
	# print("login")
	return render_template('login.html', customer=customer)


@app.route('/register', methods=['GET', 'POST'])
def register():
	# todo - in this time we have just admins
	if NO_ACCOUNTS:
		flash("فقط المسؤول يمكنه الدخول", "warning")
		return redirect(url_for('home'))
	
	if request.method == 'POST':
		form = request.form
		first_name = form['customer-first-name'].strip()
		last_name = form['customer-last-name'].strip()
		role = "customer"
		date_joined = "زبون منذ " + str(datetime.datetime.now().date())
		city = form['customer-city'].strip()
		address = form['customer-address'].strip()
		phone_number = form['customer-phone'].strip()
		backup_phone = form['customer-backup-phone'].strip()
		password = form['customer-password'].strip()
		hashed_password = bcrypt.generate_password_hash(password)
		
		with sqlite3.connect("Shopping.db") as connection:
			cursor = connection.cursor()
			try:
				cursor.execute(
					"INSERT INTO Customers(phone_number, first_name, last_name, role, date_joined, city, address, backup_phone, password) "
					"VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
					(phone_number, first_name, last_name, role, date_joined, city, address, backup_phone, hashed_password)
				)
				connection.commit()
				# successfully registered
				flash("تم التسجيل في الموقع بنجاح", category="success")
				return redirect(url_for('login'))
			except Exception as e:
				connection.rollback()
				# failed to register
				flash("حدث خطأ أثناء التسجيل للموقع" + f": {e}", category="error")
				return redirect(url_for("register"))
	
	return render_template('register.html', cities=cities)


@app.route('/forgot_password')
def forgot_password():
	return render_template('forgot_password.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
	if request.method == 'POST':
		return redirect(url_for('profile'))
	if current_user.role == "admin":
		return redirect(url_for('admin_profile'))
	return render_template('profile.html', current_user=current_user)


@app.route('/admin_profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
	if current_user.role == "admin":
		customer = False
		return render_template('admin_profile.html', current_user=current_user, customer=customer)
	return redirect(url_for('profile'))


@app.route('/admin_profile/orders', methods=['GET', 'POST'])
@login_required
def orders():
	if current_user.role == "admin":
		customer = False
		return render_template('orders.html', customer=customer)
	return redirect(url_for('profile'))


@app.route('/<ptype>/<name>/<id_num>')
def product(ptype, name, id_num):
	customer = True
	if current_user.is_authenticated and current_user.role == "admin":
		customer = False
	with sqlite3.connect('Shopping.db') as connection:
		cursor = connection.cursor()
		take_product = f"""
		select * from Products
		where id_number = {id_num}
		"""
		res_rows = cursor.execute(take_product)
		
		result = res_rows.fetchone()
		img_src = result[3][7:]
		
		# product_images = [img for img in os.listdir(result[3][:result[3].rindex("/")])]
		# img_src += f"/{product_images[0]}"
	return render_template('product.html', customer=customer, result=result, img_src=img_src)


@app.route('/admin_profile/products', methods=['GET', 'POST'])
@login_required
def products():
	if current_user.role == "admin":
		customer = False
		return render_template('products.html', customer=customer)
	return redirect(url_for('profile'))


@app.route('/admin_profile/products/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
	done = request.args.get('done')
	name = request.args.get('name')
	ptype = request.args.get('ptype')
	
	if current_user.role == "admin":
		customer = False
		if request.method == "POST":
			product_name = request.form['product-name']
			product_type = request.form['product-type']
			product_img = request.files['product-img']
			product_description = request.form['product-description']
			product_price = request.form['product-price']
			product_items_left = request.form['product-items-left']
			product_publish_year = request.form['product-publish-year']
			product_author = request.form['product-author']
			product_categories = request.form['product-categories']
			categories = [x.strip() for x in product_categories.split(',')]
			
			with sqlite3.connect("Shopping.db") as connection:
				cursor = connection.cursor()
				try:
					cursor.execute(
						"INSERT INTO Products (name, type, price, items_left, description, publish_year, author_name, categories) "
						"VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
						(product_name, product_type, product_price, product_items_left, product_description, product_publish_year, product_author, product_categories)
					)
					
					filename = secure_filename(product_img.filename)
					product_folder = 'books' if product_type == "كتب" else "clothes"
					img_path = f'static/images/{product_folder}'
					if not os.path.exists(img_path + f"/{cursor.lastrowid}"):
						os.mkdir(img_path + f"/{cursor.lastrowid}")
					img_path += f"/{cursor.lastrowid}/{filename}"
					product_img.save(img_path)
					
					cursor.execute(f"""
					update Products
					set img_path = '{img_path}'
					where id_number = {cursor.lastrowid}
					""")
					
					connection.commit()
					
					# successfully added
					flash(f"تمت إضافة ال{product_type} بنجاح", category="success")
					return redirect(url_for('add_product', done=True, name=product_name, ptype=product_type))
				except Exception as e:
					connection.rollback()
					# failed to add
					flash(f"حدث خطأ أثناء إضافة ال{product_type}" + f": {e}", category="error")
					return redirect(url_for('add_product'))
		
		# if we arrive now to add product page
		return render_template('add_product.html', customer=customer, done=done, name=name, ptype=ptype)
	# if the user is not admin
	return redirect(url_for('profile'))


@app.route('/admin_profile/products/remove_product', methods=['GET', 'POST'])
@login_required
def remove_product():
	if current_user.role == "admin":
		customer = False
		if request.method == "POST":
			product_id = request.form["search-product-id-input"]
			# if the user didn't enter any number to search for
			if product_id == "":
				flash("لم يتم إدخال أي رقم", "warning")
				return redirect(url_for('remove_product'))
			
			with sqlite3.connect("Shopping.db") as connection:
				cursor = connection.cursor()
				try:
					row_count = cursor.execute(f"""
					delete from Products
					where id_number = {product_id}
					""")
					
					connection.commit()
					if row_count.rowcount > 0:
						flash(f"تمت إزالة المنتج رقم {product_id}", "success")
					else:
						flash(f"لم يتم إيجاد منتج رقم {product_id}", "warning")
					
					return redirect(url_for('remove_product'))
				except Exception as e:
					connection.rollback()
					flash(f"حدث خطأ أثناء إزالة منتج رقم {product_id}" + f": {e}", "error")
					return redirect(url_for('remove_product'))
					
		return render_template('remove_product.html', customer=customer)
	return redirect(url_for('profile'))


@app.route('/admin_profile/products/search_update_product', methods=['GET', 'POST'])
@login_required
def search_update_product():
	if current_user.role == "admin":
		customer = False
		return render_template("search_update_product.html", customer=customer)
	return redirect(url_for('profile'))


@app.route('/admin_profile/products/update_product', methods=['GET', 'POST'])
@login_required
def update_product():
	done = request.args.get('done')
	name = request.args.get('name')
	ptype = request.args.get('ptype')
	
	if current_user.role == "admin":
		customer = False
		if request.method == "POST":
			product_id = request.form['product-id-input']
			product_name = request.form['product-name']
			product_type = request.form['product-type']
			product_img = request.files['product-img']
			# print(product_img)
			product_description = request.form['product-description']
			product_price = request.form['product-price']
			product_items_left = request.form['product-items-left']
			product_publish_year = request.form['product-publish-year']
			product_author = request.form['product-author']
			product_categories = request.form['product-categories']
			
			save_product_sql = f"""
			update Products
			set name = '{product_name}',
			type = '{product_type}',
			
			price = '{product_price}',
			items_left = {product_items_left},
			description = '{product_description}',
			publish_year = '{product_publish_year}',
			author_name = '{product_author}',
			categories = '{product_categories}'
			where id_number = {product_id}
			"""
			with sqlite3.connect("Shopping.db") as connection:
				cursor = connection.cursor()
				try:
					cursor.execute(save_product_sql)
					connection.commit()
					flash(f"تم تعديل المنتج رقم {product_id}", "success")
					# print("hi")
				except Exception as e:
					# print(e)
					connection.rollback()
					flash(f"حدث خطأ أثناء تعديل منتج رقم {product_id}" + f": {e}", "error")
					# print("what")
					return redirect(url_for('update_product'))
				# result = cursor.fetchone()
				
				return redirect(url_for('update_product', done=True, name=product_name, ptype=product_type, id_num=product_id))
		
		elif request.method == "GET":
			
			id_num = int(request.args.get('id_num'))
			search_for_id = f"""
			select * from Products
			where id_number = {id_num}
			"""
			with sqlite3.connect("Shopping.db") as connection:
				cursor = connection.cursor()
				try:
					cursor.execute(search_for_id)
					connection.commit()
					flash(f"تم إيجاد المنتج رقم {id_num}", "success")
				except Exception as e:
					connection.rollback()
					flash(f"حدث خطأ أثناء البحث عن منتج رقم {id_num}" + f": {e}", "error")
					return redirect(url_for('update_product'))
				result = cursor.fetchone()
				img_src = result[3][7:]
				product_images = [img for img in os.listdir(result[3])]
				img_src += f"/{product_images[0]}"
			return render_template('update_product.html', customer=customer, done=done, result=result, name=name, ptype=ptype, img_src=img_src)
		
		# return render_template('search_update_product.html', customer=customer, done=done, name=name, ptype=ptype)
	return redirect(url_for('profile'))


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))


@app.route('/about')
def about():
	customer = True
	if current_user.is_authenticated and current_user.role == "admin":
		customer = False
	return render_template('about.html', customer=customer)


@app.route('/contact_us')
def contact_us():
	customer = True
	if current_user.is_authenticated and current_user.role == "admin":
		customer = False
	return render_template('contact_us.html', customer=customer)


@app.route('/shopping_cart', methods=['GET', 'POST'])
def shopping_cart():
	result = session.get("cart-items")
	total = session.get("total")
	
	customer = True
	if current_user.is_authenticated and current_user.role == "admin":
		customer = False
		flash("عربة التسوق فقط للزبائن", category="warning")
		return redirect(url_for('admin_profile'))
	
	if request.method == 'POST':
		# for id_num, item in result.items():
		# 	if f"select{id_num}" in request.form.keys() and request.form[f"select{id_num}"] != "":
		# 		result[id_num] = (request.form[f"select{id_num}"], result[id_num][1])
		# session["cart-items"] = result
		# session["total"] = 0
		# for id_num, item in result.items():
		# 	session["total"] += int(item[0]) * int(item[1][4])
		#
		# if "deleted-id" in request.form.keys() and request.form["deleted-id"] != "":
		# 	# we deleted some cart items
		# 	cur = result[request.form["deleted-id"]]
		# 	session["total"] -= cur[0] * cur[1][4]
		# 	del result[request.form["deleted-id"]]
		# 	session["cart-items"] = result
		# 	return redirect(url_for('shopping_cart'))
		# el
		
		if "cart-items-input" in request.form.keys() and request.form["cart-items-input"] != "":
			total = 0
			cart_items = {}
			print(request.form)
			if request.form['cart-items-input'] != "{}":
				for item in request.form['cart-items-input'][1:-1].replace("\"", "").split(","):
					tmp = item.split(":")
					cart_items[int(tmp[0])] = tmp[1]
			# cart_items = [int(x) for x in request.form['cart-items-input'][1:-1].replace("\"", "").split(",")]
			with sqlite3.connect("Shopping.db") as connection:
				cursor = connection.cursor()
				result = {}
				for cur_id, quantity in cart_items.items():
					try:
						cursor.execute(f"""
						select * from Products
						where id_number = {cur_id}
						""")
						
						cur_res_rows = cursor.fetchone()
						# if there is already the same item in the cart
						result[cur_id] = (quantity, cur_res_rows)
						total += int(cur_res_rows[4]) * int(quantity)
					except Exception as e:
						connection.rollback()
						flash(f"error in shopping cart product num {cur_id}", "error")
						return redirect(url_for('shopping_cart'))
					
				# commit when finish the loop
				connection.commit()
				
				session["cart-items"] = result
				session["total"] = total
				print("cart items: " + str(result))
				return redirect(url_for('shopping_cart'))
			
	return render_template('shopping_cart.html', customer=customer, cart_items=session.get("cart-items"), total=session.get("total"))


# @app.route('/update_cart', methods=['GET', 'POST'])
# def update_cart():
# 	result = session.get("cart-items")
# 	if request.method == "POST":
# 		print(request.form)
# 		del result[request.form["deleted-id"]]
# 		session["cart-items"] = result
# 		print(result)
# 		return redirect(url_for('shopping_cart'))
# 	customer = True
# 	if current_user.is_authenticated and current_user.role == "admin":
# 		customer = False
# 		flash("عربة التسوق فقط للزبائن", category="warning")
# 		return redirect(url_for('admin_profile'))
#
# 	return render_template('shopping_cart.html', customer=customer, cart_items=session.get("cart-items"), total=session.get("total"))


@app.errorhandler(404)
def page_not_found(error):
	return render_template('page_not_found.html'), 404


def save_customer_func(form):
	first_name = form['customer-first-name']
	last_name = form['customer-last-name']
	city = form['customer-city']
	address = form['customer-address']
	phone_number = form['customer-phone']
	backup_phone = form['customer-backup-phone']
	password = form['customer-password']
	with sqlite3.connect("Shopping.db") as connection:
		cursor = connection.cursor()
		try:
			cursor.execute(
				"INSERT INTO Customers "
				"VALUES(?, ?, ?, ?, ?, ?, ?)",
				(phone_number, first_name, last_name, city, address, backup_phone, password)
			)
			connection.commit()
			# successfully registered
			flash("Succes", 'success')
		except Exception as e:
			# print(e)
			connection.rollback()
			# failed to register
			flash("Error: " + str(e), 'error')
			return False
	return True


if __name__ == "__main__":
	# webbrowser.open("http://127.0.0.1:5000/home")
	# app.run()
	# create_table()
	# print(app.url_map)
	app.run(host="0.0.0.0", debug=True)
	
import os
import sqlite3
import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, AnonymousUserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from flask import render_template, jsonify, Flask, request, redirect, url_for, flash, session
from database_handling import *

app = Flask(__name__)
app.secret_key = 'lakjfpoek[gf;sldg165478'
app.config['DEBUG'] = True

# app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///Shopping.db'
# db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

NO_ACCOUNTS = False


class User(UserMixin):
	def __init__(self, id_number, phone_number, first_name, last_name, role, date_joined, city, address, backup_phone, password, email):
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
		self.email = email
	
	def get_id(self):
		return self.id_number
	
	def is_admin(self):
		return True if self.role == "admin" else False


def check_role():
	if current_user.is_anonymous:
		user_role = "guest"
	else:
		user_role = current_user.role
		
	return user_role


@app.route('/home')
def home():
	# if the current user is guest or registered customer then True if admin then False
	user_role = check_role()
	
	return render_template('home.html', user_role=user_role)


@app.route('/books')
def books():
	# if the current user is guest or registered customer then True if admin then False
	user_role = check_role()
	
	with sqlite3.connect("Shopping.db") as connection:
		cursor = connection.cursor()
		try:
			# retrieve all the products that their type is "كتب" to get all the books in the website
			cursor.execute("""
			select * from Products
			where type = 'كتب'
			""")
			
			all_books = cursor.fetchall()
			connection.commit()
		except Exception as e:
			connection.rollback()
			flash("خطأ في تحميل الكتب\nنوع الخطأ: " + str(e), "error")
			return redirect(url_for('books'))
	
	# todo - this for FILTERS feature, authors=authors, publishes=publishes, publishers=publishers, other=other)
	return render_template('books.html', products=all_books, user_role=user_role)


@app.route('/clothes')
def clothes():
	user_role = check_role()
	return render_template('clothes.html', products=clothes_lst, user_role=user_role)


@login_manager.user_loader
def load_user(user_id):
	# this function to load user using its id number
	with sqlite3.connect("Shopping.db") as connection:
		cursor = connection.cursor()
		try:
			cursor.execute(f"""
		        select *
		        from Customers
		        where id_number = '{user_id}'
		        """)
			result = cursor.fetchone()
			connection.commit()
		except Exception as e:
			connection.rollback()
			flash("خطأ في الحصول على المستخدم\nنوع الخطأ: " + str(e), "error")
			return None
		
		# if the result is empty return None because there is no user that have this id number
		if result:
			return User(*result)
		else:
			return None


@app.route('/login', methods=['POST', 'GET'])
def login():
	if request.method == 'POST':
		# checking which method the user want to login with
		login_method = request.form['login-method']
		email, phone_number = "", ""
		if login_method == "email":
			email = request.form['customer-email']
		elif login_method == "phone":
			phone_number = request.form['customer-phone']
		password = request.form['customer-password']
		
		with sqlite3.connect('Shopping.db') as connection:
			cursor = connection.cursor()
			if login_method == "phone":
				# retrieve the user that has this phone number
				check_user_existence = f"""
	                select *
	                from Customers
	                where phone_number = '{phone_number}'
	                """
			else:
				# retrieve the user that has this email
				check_user_existence = f"""
	                select *
	                from Customers
	                where email = '{email}'
	                """
			
			res_rows = cursor.execute(check_user_existence)
			# check - fetchall or fetchone, which better?
			res_rows = res_rows.fetchall()
			connection.commit()
		# if we found more than one user with this "unique" info (will not happen, but in case...)
		if len(res_rows) == 1:
			# if we still don't have any users except admins
			if NO_ACCOUNTS and res_rows[0][4] != "admin":
				flash("فقط المسؤول يمكنه تسجيل الدخول", "warning")
				return redirect(url_for('home'))
			# checking the entered password with the stored password
			# if they are identical then login the current user
			if bcrypt.check_password_hash(res_rows[0][-2], password):
				# load the user with the found id number
				user = load_user(res_rows[0][0])
				# login the current user
				login_user(user)
				# todo - should I concatenate both anonymous and stored carts? I think NO
				# store the current cart items in the database to include them in customer's database
				# with sqlite3.connect("Shopping.db") as connection:
				# 	cursor = connection.cursor()
				# 	try:
				#
				# 	except Exception as e:
				# 		connection.rollback()
				# 		flash("فشل تحديث سلة المشتريات الحالية\nنوع الخطأ: " + str(e), "error")
				# 		# todo - what happens when adding anonymous cart to stored cart
				flash("تم تسجيل الدخول بنجاح!", category="success")
				# if the user is an admin then go to admin profile, otherwise to normal profile
				if current_user.role == "admin":
					return redirect(url_for('admin_profile'))
				return redirect(url_for('profile'))
		# if there is no user has these unique info, then go and register the new user
		elif len(res_rows) == 0:
			flash("لم تقم بالتسجيل في الموقع من قبل, تفضّل بالتسجيل في الموقع", category="warning")
			return redirect(url_for('register'))
		# if we found more than one user with the same info
		else:
			flash("حدث خطأ أثناء تسجيل الدخول (هنالك أكثر من مستخدم لديهم نفس رقم الهاتف أو البريد الإلكتروني", "error")
			return redirect(url_for('login'))
			
	# if the current user is already logged in, then go to profile
	if current_user.is_authenticated:
		if current_user.role == "admin":
			return redirect(url_for('admin_profile'))
		return redirect(url_for('profile'))
	
	user_role = check_role()
	
	return render_template('login.html', user_role=user_role)


@app.route('/register', methods=['GET', 'POST'])
def register():
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
		email = form['customer-email'].strip()
		backup_phone = form['customer-backup-phone'].strip()
		password = form['customer-password'].strip()
		hashed_password = bcrypt.generate_password_hash(password)
		
		with sqlite3.connect("Shopping.db") as connection:
			cursor = connection.cursor()
			try:
				cursor.execute("""
				INSERT INTO Customers(phone_number, first_name, last_name, role, date_joined, city, address, backup_phone, password, email)
				VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""",(phone_number, first_name, last_name, role, date_joined, city, address, backup_phone, hashed_password, email)
				)
				# todo - should I commit 2 times?
				connection.commit()
				# make initial cart items entry for the new customer
				cursor.execute(f"""
				insert into Cart_Items(customer_id)
				values({cursor.lastrowid})
				""")
				connection.commit()
				# successfully registered
				flash("تم التسجيل في الموقع بنجاح", category="success")
			except Exception as e:
				connection.rollback()
				# failed to register
				flash("حدث خطأ أثناء التسجيل للموقع" + f": {e}", category="error")
				return redirect(url_for("register"))
			user = load_user(cursor.lastrowid)
			login_user(user)
			
			return redirect(url_for('profile'))
	
	return render_template('register.html', cities=cities, customer=True)


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
	return render_template('profile.html', current_user=current_user, customer=True)


@app.route('/admin_profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
	if current_user.role == "admin":
		return render_template('admin_profile.html', current_user=current_user, customer=False)
	return redirect(url_for('profile'))


@app.route('/profile/orders', methods=['GET', 'POST'])
@login_required
def orders():
	# the admin cannot enter the customer orders page
	if current_user.role == "admin":
		return redirect(url_for('all_customers_orders'))
	
	# retrieve all the orders of the current user
	with sqlite3.connect('Shopping.db') as connection:
		cursor = connection.cursor()
		try:
			cursor.execute(f"""
			select * from Orders
			where customer_id = {current_user.id_number}
			""")
			orders_result = cursor.fetchall()
			connection.commit()
		except Exception as e:
			connection.rollback()
			flash("problem with retrieving orders from database, error: " + str(e), "error")
			return redirect(url_for('profile'))
		
	# check - some parsing of each cart items, because it is as string!
	all_orders = [order[:-2] + (convert_str_to_dic(order[-2]), order[-1]) for order in orders_result]
	return render_template("orders.html", customer=True, all_orders=all_orders)


@app.route('/admin_profile/all_customers_orders', methods=['GET', 'POST'])
@login_required
def all_customers_orders():
	# the customer cannot enter the admin orders page
	if current_user.role == "customer":
		return redirect(url_for('orders'))
	
	# retrieve all the orders of all the users for the admin to handle
	with sqlite3.connect('Shopping.db') as connection:
		cursor = connection.cursor()
		try:
			cursor.execute("""
			select * from Orders
			""")
			orders_result = cursor.fetchall()
			connection.commit()
		except Exception as e:
			connection.rollback()
			flash("problem with retrieving orders from database, error: " + str(e), "error")
			return redirect(url_for('admin_profile'))
	# all_orders = [convert_str_to_dic(order[-1]) for order in orders_result]
	
	# check - some parsing of each cart items, because it is as string!
	all_orders = [order[:-1] + (convert_str_to_dic(order[-2]),) for order in orders_result]
	return render_template('all_customers_orders.html', customer=False, all_orders=all_orders)


@app.route('/<ptype>/<name>/<id_num>')
def product(ptype, name, id_num):
	user_role = check_role()
	
	# retrieve the info for the current product
	with sqlite3.connect('Shopping.db') as connection:
		cursor = connection.cursor()
		try:
			res_rows = cursor.execute(f"""
				select * from Products
				where id_number = {id_num}
				""")
		
			result = res_rows.fetchone()
			connection.commit()
		except Exception as e:
			connection.rollback()
			flash("خطأ في تحميل صفحة المنتج\nنوع الخطأ: " + str(e), "error")
			return redirect(request.referrer)
		
		# take the product's image src path
		img_src = result[3][7:]
	
	return render_template('product.html', user_role=user_role, result=result, img_src=img_src)


@app.route('/admin_profile/handling_products', methods=['GET', 'POST'])
@login_required
def handling_products():
	# just the admin can go to products handling page
	if current_user.role == "admin":
		return render_template('handling_products.html', customer=False)
	return redirect(url_for('profile'))


@app.route('/admin_profile/handling_products/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
	if current_user.role != "admin":
		return redirect(url_for('profile'))
		
	done = request.args.get('done')
	name = request.args.get('name')
	ptype = request.args.get('ptype')
	
	# we enter this if when adding product
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
		
		# add the entered product info to the database
		with sqlite3.connect("Shopping.db") as connection:
			cursor = connection.cursor()
			try:
				cursor.execute(
					"INSERT INTO Products (name, type, price, items_left, description, publish_year, author_name, categories) "
					"VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
					(product_name, product_type, product_price, product_items_left, product_description, product_publish_year, product_author,
					 product_categories)
				)
				
				# validating filename and creating img src path to store in database
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
	return render_template('add_product.html', customer=False, done=done, name=name, ptype=ptype)


@app.route('/admin_profile/handling_products/remove_product', methods=['GET', 'POST'])
@login_required
def remove_product():
	# just the admin can enter removing product page
	if current_user.role != "admin":
		return redirect(url_for('profile'))
		
	if request.method == "POST":
		product_id = request.form["search-product-id-input"]
		# if the user didn't enter any number to search for
		if product_id == "":
			flash("لم يتم إدخال أي رقم", "warning")
			return redirect(url_for('remove_product'))
		
		with sqlite3.connect("Shopping.db") as connection:
			cursor = connection.cursor()
			try:
				# deleting the wanted product
				row_count = cursor.execute(f"""
					delete from Products
					where id_number = {product_id}
					""")
				
				connection.commit()
				# if the process returned some affected rows then we deleted the wanted product
				if row_count.rowcount > 0:
					flash(f"تمت إزالة المنتج رقم {product_id}", "success")
				# if there is no affected rows then there is no product with this product number
				else:
					flash(f"لم يتم إيجاد منتج رقم {product_id}", "warning")
				return redirect(url_for('remove_product'))
			except Exception as e:
				connection.rollback()
				flash(f"حدث خطأ أثناء إزالة منتج رقم {product_id}" + f": {e}", "error")
				return redirect(url_for('remove_product'))
	
	return render_template('remove_product.html', customer=False)


@app.route('/admin_profile/handling_products/search_update_product', methods=['GET', 'POST'])
@login_required
def search_update_product():
	if current_user.role == "admin":
		return render_template("search_update_product.html", customer=False)
	return redirect(url_for('profile'))


@app.route('/admin_profile/handling_products/update_product', methods=['GET', 'POST'])
@login_required
def update_product():
	# just the admin can enter update product page
	if current_user.role != "admin":
		return redirect(url_for('profile'))
		
	done = request.args.get('done')
	name = request.args.get('name')
	ptype = request.args.get('ptype')
	
	if request.method == "POST":
		product_id = request.form['product-id-input']
		product_name = request.form['product-name']
		product_type = request.form['product-type']
		product_img = request.files['product-img']
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
			except Exception as e:
				connection.rollback()
				flash(f"حدث خطأ أثناء تعديل منتج رقم {product_id}" + f": {e}", "error")
				return redirect(url_for('update_product'))
			
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
		return render_template('update_product.html', customer=False, done=done, result=result, name=name, ptype=ptype, img_src=img_src)


@app.route('/shopping_cart', methods=['GET', 'POST'])
def shopping_cart():
	# prevent admin from entering the shopping cart, it is for customeeeers
	if current_user.is_authenticated and current_user.role == "admin":
		flash("عربة التسوق فقط للزبائن", category="warning")
		return redirect(url_for('admin_profile'))
		
	if request.method == 'POST':
		if "cart-items-input" in request.form.keys() and request.form["cart-items-input"] != "":
			total = 0
			cart_items = {}
			# parse the cart items string to real dictionary with id as key and (quantity and item info) as value
			if request.form['cart-items-input'] != "{}":
				for item in request.form['cart-items-input'][1:-1].replace("\"", "").split(","):
					tmp = item.split(":")
					cart_items[int(tmp[0])] = tmp[1]
					
			# retrieve all the products corresponds to the cart items, to display them
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
						result[cur_id] = (int(quantity), cur_res_rows)
						total += int(cur_res_rows[4]) * int(quantity)
					except Exception as e:
						connection.rollback()
						flash(f"error in shopping cart product num {cur_id} " + str(e), "error")
						return redirect(url_for('home'))
				
				# commit when finish the loop
				connection.commit()
				# store the cart items and their value in the session
				# todo - how can I do this!!!
				# try:
				# 	cursor.execute(f"""
				#
				# 	""")
				# except Exception as e:
				# 	flash("حدث خطأ أثناء تحميل سلة التسوق\nنوع الخطأ: " + str(e), "error")
				# 	return redirect(url_for('home'))
				
				session["cart-items"] = result
				session["total"] = total
				return redirect(url_for('shopping_cart'))
	
	return render_template('shopping_cart.html', customer=True, cart_items=session.get("cart-items"), total=session.get("total"))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
	# admin go awaaaay
	if not current_user.is_anonymous and current_user.role == "admin" or (session.get("cart-items") == {} and session.get("total") == 0):
		return redirect(url_for('home'))
	
	cart_items = session.get("cart-items")
	total = session.get("total")
	# taking all the user's info for the order
	if request.method == "POST":
		first_name = request.form['customer-first-name'].strip()
		last_name = request.form['customer-last-name'].strip()
		city = request.form['customer-city'].strip()
		address = request.form['customer-address'].strip()
		email = request.form['customer-email'].strip()
		phone_number = request.form['customer-phone'].strip()
		backup_phone = request.form['customer-backup-phone'].strip()
		
		role = "customer" if not current_user.is_anonymous and current_user.role == "customer" else "guest"
		# تم تجهيز الطلب
		# الطلب في الطريق إليك
		# تم توصيل الطلب
		status = "تم تأكيد الطلب"
		total_amount = session.get("total")
		shipping = 25
		total_amount = str(int(total_amount) + shipping)
		cart_items = session.get("cart-items")
		date_purchased = datetime.datetime.now()
		date_purchased = date_purchased.strftime("%Y-%m-%d %H:%M")
		
		with sqlite3.connect("Shopping.db") as connection:
			cursor = connection.cursor()
			# iterate over all th ecart items to store in the order info
			for id_num, (quantity, item) in cart_items.items():
				try:
					cursor.execute(f"""
					select * from Products
					where id_number = {id_num}
					""")
					res_row = cursor.fetchone()
					if res_row is None:
						raise Exception(f"لا يوجد منتج بإسم {item[1]}")
					if int(quantity) <= res_row[5]:
						# we have the enough amount to sell
						cursor.execute(f"""
						update Products
						set items_left = items_left - {quantity}
						where id_number = {id_num}
						""")
						continue
					else:
						# we don't have the enough amount to sell
						# flash(f"لا يوجد كمية كافية من المنتج {item[1]}", "warning")
						raise Exception(f"لا يوجد كمية كافية من المنتج {item[1]}")
				except Exception as e:
					connection.rollback()
					flash(f"حدث خطأ أثناء الدفع\nنوع الخطأ: " + str(e), "error")
					return redirect(url_for('checkout'))
			
			session["total"] = 0
			session["cart-items"] = {}
			
			# store the order in Orders SQL table
			if not current_user.is_anonymous and current_user.role == "customer":
				cursor.execute("""
				insert into Orders(customer_id, customer_first_name, customer_last_name, role, city, address, email, backup_phone, customer_phone_number, order_date, total_amount, status, cart_items)
				values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""", (current_user.id_number, first_name, last_name, role, city, address, email, backup_phone, phone_number, date_purchased, total_amount, status, str(cart_items)))
			#  guest
			else:
				cursor.execute("""
				insert into Orders(customer_first_name, customer_last_name, role, city, address, email, backup_phone, customer_phone_number, order_date, total_amount, status, cart_items)
				values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
				""", (first_name, last_name, role, city, address, email, backup_phone, phone_number, date_purchased, total_amount, status, str(cart_items)))
			
			connection.commit()
		
		return render_template("order_approved.html", customer=True)
	cur_user = current_user if not current_user.is_anonymous else None
	return render_template('checkout.html', cities=cities, customer=True, total=total, cur_user=cur_user)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))


@app.route('/about')
def about():
	user_role = check_role()
	return render_template('about.html', user_role=user_role)


@app.route('/contact_us')
def contact_us():
	user_role = check_role()
	return render_template('contact_us.html', user_role=user_role)


# converting cart_items from Orders SQL table from string to dictionary to use it in creating orders page
def convert_str_to_dic(string: str) -> dict:
	keys = []
	values = []
	# string = "{'10': ('2', (10, 'كتاب1', 'كتب', 'static/images/books/10/product2.png', '30', 12, 'asdfghjk', '2000', 'مش أنا', 'قصص أطفال')), '9': ('3', (9, 'كتاب', 'كتب', 'static/images/books/9/product1.png', '50', 5, 'asd', '2022', 'أنا', 'روايات'))}"
	tmp = string[1:-1].split(":")
	ind = -1
	for i, x in enumerate(tmp):
		last_one = True
		if i == 0:
			keys.append(x[1:-1])
		elif i != len(tmp) - 1:
			ind = x.rindex(",")
			keys.append(x[ind + 1:].strip()[1:-1])
			last_one = False
			
		if i != 0:
			if last_one:
				value = x[:-1].strip().replace("\'", "")
			else:
				value = x[:ind].strip()[1:-1].replace("\'", "")
			item = []
			value = value[1:] if value[0] == "(" else value
			indx = value.index(",")
			# print(value)
			tup = value[:indx].strip(), value[indx + 1:].strip()
			for j, v in enumerate(tup[1][1:-1].split(",")):
				if j == 0 or j == 5:
					item.append(int(v.strip()))
				else:
					item.append(v.strip())
			
			value = int(tup[0]), tuple(item)
			values.append(value)
	
	dic = {keys[i]: values[i] for i in range(len(keys))}
	# print(dic)
	return dic


@app.errorhandler(404)
def page_not_found(error):
	return render_template('page_not_found.html'), 404


if __name__ == "__main__":
	# webbrowser.open("http://127.0.0.1:5000/home")
	# app.run()
	# create_table()
	# print(app.url_map)
	app.run(host="0.0.0.0", debug=True)

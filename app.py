import os
import sqlite3
import smtplib

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_login import UserMixin, LoginManager, login_required, current_user
from flask import render_template, Flask, request, redirect, url_for, flash
from blueprints.admin import admin_bp
from blueprints.shopping_cart_handler import shopping_cart_bp
from blueprints.products_handling import products_handling_bp
from blueprints.users_handling import user_bp
from blueprints.user_profile import user_profile_bp
from helpers import check_role, send_error, convert_str_to_dic, User, r2_handler
from extensions import bcrypt, login_manager


app = Flask(__name__)
bcrypt.init_app(app)

app.register_blueprint(admin_bp)
app.register_blueprint(shopping_cart_bp)
app.register_blueprint(products_handling_bp)
app.register_blueprint(user_bp)
app.register_blueprint(user_profile_bp)

app.secret_key = os.getenv("SHOPPING_APP_KEY")
app.config['DEBUG'] = True

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///Shopping.db'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle' : 300}

SQL_PASS = ""
SQLALCHEMY_DATABASE_URI = f"mysql+mysqldb://irtekaa:{SQL_PASS}@irtekaa.mysql.pythonanywhere-services.com/Shopping"
# app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

db = SQLAlchemy(app)

engine = create_engine('sqlite:///Shopping.db')

login_manager.init_app(app)
login_manager.login_view = "login"


# class Customers(db.Model):
# 	__tablename__ = "customers"
# 	id_number = db.Column(db.Integer, primary_key=True, autoincrement=True)
# 	phone_number = db.Column(db.NVARCHAR(10), unique=True)
# 	first_name = db.Column(db.NVARCHAR(15))
# 	last_name = db.Column(db.NVARCHAR(15))
# 	role = db.Column(db.NVARCHAR(10))
# 	date_joined = db.Column(db.NVARCHAR(20))
# 	city = db.Column(db.NVARCHAR(20))
# 	address = db.Column(db.NVARCHAR(50))
# 	backup_phone = db.Column(db.NVARCHAR(10))
# 	password = db.Column(db.NVARCHAR(80))
#   email = db.Column(db.NVARCHAR(50), unique=True)
#   forgot_password = db.Column(db.Integer)


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
            send_error(e, "خطأ في الحصول على المستخدم")
            connection.rollback()
            flash("خطأ في الحصول على المستخدم\nنوع الخطأ: " + str(e), "error")
            return None

        # if the result is empty return None because there is no user that have this id number
        if result:
            return User(*result)
        else:
            return None


@app.route("/")
def index():
    return redirect('/home')


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
            all_books = [book[:3] + (book[3].split('&'),) + book[4:] for book in all_books]
            return render_template('books.html', products=all_books, user_role=user_role)
        except Exception as e:
            send_error(e, "خطأ في تحميل الكتب")
            connection.rollback()
            flash("خطأ في تحميل الكتب\nنوع الخطأ: " + str(e), "error")
            return redirect(request.referrer)


@app.route('/clothes')
def clothes():
    # if NO_CLOTHES:
    #     return redirect(url_for('home'))
    user_role = check_role()
    # check this
    clothes_lst = []
    return render_template('clothes.html', products=clothes_lst, user_role=user_role)


@app.route('/gifts_corner')
def gifts_corner():
    # if NO_CLOTHES:
    #     return redirect(url_for('home'))
    user_role = check_role()

    with sqlite3.connect("Shopping.db") as connection:
        cursor = connection.cursor()
        try:
            # retrieve all the products that their type is "ركن الهدايا" to get all the gifts in the website
            cursor.execute("""
            select * from Products
            where type = 'ركن الهدايا'
            """)

            all_gifts_corner = cursor.fetchall()
            connection.commit()
            all_gifts_corner = [gift[:3] + (gift[3].split('&'),) + gift[4:] for gift in all_gifts_corner]
            return render_template('gifts_corner.html', products=all_gifts_corner, user_role=user_role)
        except Exception as e:
            send_error(e, "خطأ في تحميل ركن الهدايا")
            connection.rollback()
            flash("خطأ في تحميل ركن الهدايا\nنوع الخطأ: " + str(e), "error")
            return redirect(request.referrer)


@app.route('/<ptype>/<id_num>', methods=['POST', 'GET'])
def product(ptype, id_num):
    user_role = check_role()

    # todo - this for wishlist feature
    # if request.method == 'POST' and request.form.get('wish-product-id') and request.form.get(
    #         'wish-product-id').strip() != "":
    #     # wish the product
    #     with sqlite3.connect("Shopping.db") as connection:
    #         cursor = connection.cursor()
    #         try:
    #             cursor.execute(f"""
    #             update Products
    #             set wished_num = wished_num + 1
    #             where id_number = {id_num}
    #             """)
    #             connection.commit()
    #             return redirect(request.referrer)
    #         except Exception as e:
    #             send_error(e)
    #             flash("حدث خطأ أثناء الإهتمام بالمنتج\n خطأ: " + str(e), "error")
    #             return redirect(request.referrer)

    # add to cart functionality
    if request.method == "POST" and user_role == "customer":
        product_id = int(request.form['cart-item-id-update'])
        cart_items_tmp = request.form['cart-items-update']
        product_price = float(request.form['item-price-update'])
        cart_items = {}
        for item in cart_items_tmp[1:-1].replace("\"", "").split(","):
            tmp = item.split(":")
            cart_items[int(tmp[0])] = tmp[1]

    
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
            send_error(e, "خطأ في تحميل صفحة المنتج")
            connection.rollback()
            flash("خطأ في تحميل صفحة المنتج\nنوع الخطأ: " + str(e), "error")
            return redirect(request.referrer)

        # take the product's image src path
        img_src = result[3].split("&")
        print(img_src)

    return render_template('product.html', user_role=user_role, result=result, images=img_src)


@app.route('/<parent>/order_info/<order_id>', methods=['GET', 'POST'])
@login_required
def order_info(parent, order_id):
    with sqlite3.connect("Shopping.db") as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(f"""
            select * from Orders
            where id_number = {order_id}
            """)

            result = cursor.fetchone()
            connection.commit()
        except Exception as e:
            send_error(e, "خطأ في تحميل صفحة الطلب")
            flash("حدث خطأ أثناء تحميل صفحة الطلب\n خطأ: " + str(e), "error")
            connection.rollback()
            return redirect(request.referrer)
    result = result[:-2] + (convert_str_to_dic(result[-2]), result[-1])

    return render_template('order_info.html', order=result, cur_user=current_user, user_role=current_user.role)


@app.route('/about')
def about():
    user_role = check_role()
    return render_template('about.html', user_role=user_role)


@app.route('/contact_us')
def contact_us():
    user_role = check_role()
    return render_template('contact_us.html', user_role=user_role)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


if __name__ == "__main__":
    # for rule in app.url_map.iter_rules():
    #     print(f"Endpoint: {rule.endpoint}, URL: {rule.rule}")
    app.run(host="0.0.0.0", debug=True)
    # Print all registered routes in Flask
    # app.run()

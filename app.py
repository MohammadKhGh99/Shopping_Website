import os
import sqlite3
import datetime
import smtplib
import string
import random
import shutil

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from flask import render_template, Flask, request, redirect, url_for, flash, session
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

project_folder = os.path.expanduser(os.path.abspath(os.path.curdir))  # adjust as appropriate
load_dotenv(os.path.join(project_folder, '.env'))

app = Flask(__name__)
app.secret_key = os.getenv("SHOPPING_APP_KEY")
app.config['DEBUG'] = True

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///Shopping.db'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle' : 300}

SQL_PASS = ""
SQLALCHEMY_DATABASE_URI = f"mysql+mysqldb://irtekaa:{SQL_PASS}@irtekaa.mysql.pythonanywhere-services.com/Shopping"
# app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

db = SQLAlchemy(app)

engine = create_engine('sqlite:///Shopping.db')
GMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

cities = sorted(open("cities.txt", "r", encoding="utf8").readlines())
statuses = ["تم تأكيد الطلب", "تم تجهيز الطلب", "تم التوصيل"]
types = ["كتب", "أزياء", "ركن الهدايا"]
types_dict = {"كتب": "books", "أزياء": "clothes", "ركن الهدايا": "gifts_corner"}


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


class User(UserMixin):
    def __init__(self, id_number, phone_number, first_name, last_name, role, date_joined, city, address, backup_phone,
                 password, email, forgot_password=0):
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
        self.forgot_password = forgot_password

    def get_id(self):
        return self.id_number

    def is_admin(self):
        return True if self.role == "admin" else False


def send_email(sender, app_password, to, subject, message_text, msg_type):
    # Create a secure connection to the Gmail SMTP server
    # with smtplib.SMTP('smtp.gmail.com', 587) as smtp_server:
    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_server.starttls()

    # Log in to your Gmail account using the App Password
    smtp_server.login(sender, app_password)

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(message_text, msg_type))

    # send email
    smtp_server.send_message(msg)

    smtp_server.quit()


def send_error(e, subject):
    send_email("mohammad.gh454@gmail.com", 
               GMAIL_PASS,
               "m7md.gh.99@hotmail.com",
               subject,
               str(e),
               "plain")


def check_role():
    if current_user.is_anonymous:
        user_role = "guest"
    else:
        user_role = current_user.role

    return user_role


@app.route("/")
def index():
    # with engine.connect() as connection:
    #     result = connection.execute(text("SELECT * FROM Customers"))
    #     for row in result:
    #         print(row)
    # Redirect to the actual homepage
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


@app.route('/login', methods=['POST', 'GET'])
def login():
    user_role = check_role()
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
            # if NO_ACCOUNTS and res_rows[0][4] != "admin":
            #     flash("فقط المسؤول يمكنه تسجيل الدخول", "warning")
            #     return redirect(request.referrer)
            # checking the entered password with the stored password
            # if they are identical then login the current user
            if bcrypt.check_password_hash(res_rows[0][-3], password):
                # load the user with the found id number
                user = load_user(res_rows[0][0])
                if user.forgot_password == 1:
                    # todo - change password for user
                    return redirect(url_for('new_password', phone_number=res_rows[0][1]))
                # login the current user
                login_user(user)
                flash("تم تسجيل الدخول بنجاح!", category="success")
                # if the user is an admin then go to admin profile, otherwise to normal profile
                if user_role == "admin":
                    return redirect(url_for('admin_profile'))
                return redirect(url_for('profile'))
            else:
                flash("خطأ في إحدى الخانات (رقم الهاتف/البريد الإلكتروني أو كلمة المرور) الرجاء المحاولة مرة أخرى", "warning")
                return redirect(request.referrer)
        # if there is no user has these unique info, then go and register the new user
        elif len(res_rows) == 0:
            flash("لم تقم بالتسجيل في الموقع من قبل, تفضّل بالتسجيل في الموقع", category="warning")
            return redirect(url_for('register'))
        # if we found more than one user with the same info
        else:
            flash("حدث خطأ أثناء تسجيل الدخول (هنالك أكثر من مستخدم لديهم نفس رقم الهاتف أو البريد الإلكتروني)", "error")
            return redirect(url_for('login'))

    # if the current user is already logged in, then go to profile
    if current_user.is_authenticated:
        if user_role == "admin":
            return redirect(url_for('admin_profile'))
        return redirect(url_for('profile'))

    return render_template('login.html', user_role=user_role)


@app.route('/register', methods=['GET', 'POST'])
def register():
    user_role = check_role()
    # registered users cannot register while they are logged in
    if user_role != "guest":
        return redirect(url_for('profile'))

    # if NO_ACCOUNTS:
    #     flash("فقط المسؤول يمكنه الدخول", "warning")
    #     return redirect(request.referrer)

    if request.method == 'POST':
        form = request.form
        first_name = form['customer-first-name'].strip()
        last_name = form['customer-last-name'].strip()
        role = "customer"
        date_joined = "زبون منذ " + str(datetime.datetime.now().date())
        city = form['customer-city'].strip()
        address = form['customer-address'].strip()
        phone_number = form['customer-phone'].strip()
        if phone_number == "0543818223":
            role = "admin"
        email = form['customer-email'].strip()
        backup_phone = form['customer-backup-phone'].strip()
        password = form['customer-password'].strip()
        hashed_password = bcrypt.generate_password_hash(password)

        with sqlite3.connect("Shopping.db") as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                INSERT INTO Customers(phone_number, first_name, last_name, 
                                      role, date_joined, city, address, 
                                      backup_phone, password, email, forgot_password)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (phone_number, first_name, last_name,
                                  role, date_joined, city, address,
                                  backup_phone, hashed_password, email, 0))
                connection.commit()
                # successfully registered
                flash("تم التسجيل في الموقع بنجاح", category="success")
                user = load_user(cursor.lastrowid)
                login_user(user)
                # notify admin of new user registration
                send_email("mohammad.gh454@gmail.com", GMAIL_PASS,
                           "m7md.gh.99@hotmail.com",
                           "تم تسحيل زبون جديد",
                           f"""
                           زبون جديد بإسم {first_name} {last_name}\n
                            email: {email}\nphone: {phone_number}
                            """, "plain")
                return redirect(url_for('profile'))
            except Exception as e:
                send_error(e, "خطأ في التسجيل للموقع")
                connection.rollback()
                # failed to register
                flash("حدث خطأ أثناء التسجيل للموقع" + f": {e}", category="error")
                return redirect(request.referrer)

    user_role = check_role()
    return render_template('register.html', cities=cities, user_role=user_role)


@app.route('/forgot_password', methods=['POST', 'GET'])
def forgot_password():
    if request.method == "POST":
        customer_email = request.form['customer-email'].strip()
        customer_phone = request.form['customer-phone'].strip()
        login_method = request.form['login-method']

        with sqlite3.connect("Shopping.db") as connection:
            cursor = connection.cursor()
            try:
                chars = string.ascii_letters + string.digits
                unique_token = ''.join(random.choice(chars) for _ in range(10))
                if login_method == "phone":
                    cursor.execute(f"""
                    select * from Customers
                    where phone_number = '{customer_phone}'
                    """)
                    wanted_user = cursor.fetchone()
                    user_fullname = wanted_user[2] + " " + wanted_user[3]
                    temp_password = bcrypt.generate_password_hash(unique_token).decode('utf-8')
                    cursor.execute(f"""
                    update Customers
                    set password = '{temp_password}',
                    forgot_password = 1
                    where phone_number = '{customer_phone}'
                    """)
                    customer_email = wanted_user[10]
                else:
                    cursor.execute(f"""
                    select * from Customers
                    where email = '{customer_email}'
                    """)
                    wanted_user = cursor.fetchone()
                    user_fullname = wanted_user[2] + " " + wanted_user[3]
                    cursor.execute(f"""
                    update Customers
                    set password = '{bcrypt.generate_password_hash(unique_token)}',
                    forgot_password = 1
                    where email = '{customer_email}'
                    """)
                connection.commit()
                send_email("mohammad.gh454@gmail.com", GMAIL_PASS,
                        customer_email,
                        "استعادة كلمة المرور",
                        f"""
                        <p dir="rtl" style="text-align: center">
                            السلام عليكم {user_fullname}
                            <br><br>
                            كلمة المرور المؤقتة الخاصة بك هي
                            <br><br>
                            <b style="font_size: 1.2em; background-color: #bdbcbc">
                                {unique_token}
                            </b>
                        </p> 
                        """, "html")
                flash("تم إرسال كلمة المرور المؤقتة إلى البريد الإلكتروني", "success")
                return redirect(url_for('login'))
            except Exception as e:
                send_error(e, "خطأ في استعادة كلمة المرور")
                connection.rollback()
                flash("حدث خطأ أثناء استعادة كلمة المرور\n خطأ: " + str(e), "error")
                return redirect(request.referrer)
    return render_template('forgot_password.html')


@app.route('/new_password', methods=['POST', 'GET'])
def new_password():
    if check_role() != "guest":
        flash("يجب تسجيل الخروج أولاً", "warning")
        return redirect(url_for('profile'))
    if request.method == "POST":
        new_password = request.form['new-password']
        new_password_confirm = request.form['confirm-password']
        phone_number = request.args.get('phone_number')

        if new_password != new_password_confirm:
            flash("كلمة المرور غير متطابقة", "warning")
            return redirect(request.referrer)
        with sqlite3.connect("Shopping.db") as connection:
            cursor = connection.cursor()
            new_hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            try:
                cursor.execute(f"""
                update Customers
                set password = '{new_hashed_password}',
                forgot_password = 0
                where phone_number = '{phone_number}'
                """)
                connection.commit()
                flash("تم تغيير كلمة المرور بنجاح", "success")
                return redirect(url_for('login'))
            except Exception as e:
                send_error(e, "خطأ في تغيير كلمة المرور")
                connection.rollback()
                flash("حدث خطأ أثناء تغيير كلمة المرور\n خطأ: " + str(e), "error")
                return redirect(request.referrer)
    return render_template('new_password.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_role = check_role()
    if request.method == 'POST':
        form = request.form
        new_fullname = form['customer-fullname'].strip().split(" ")
        new_first_name = new_fullname[0].strip()
        new_last_name = ' '.join(new_fullname[1:]).strip()

        new_phone_number = form['customer-phone'].strip()
        new_backup_phone = form['customer-backup-phone'].strip()
        new_email = form['customer-email'].strip()
        # changing password as 'forgot password' feature, not here
        new_city = form['customer-city'].strip()
        new_address = form['customer-address'].strip()

        with sqlite3.connect("Shopping.db") as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(f"""
                update Customers
                set first_name = '{new_first_name}',
                last_name = '{new_last_name}',
                phone_number = '{new_phone_number}',
                backup_phone = '{new_backup_phone}',
                email = '{new_email}',
                city = '{new_city}',
                address = '{new_address}'
                where id_number = {current_user.id_number}
                """)
                connection.commit()
                flash("تم تحديث البيانات بنجاح", "success")
                return redirect(url_for('profile'))
            except Exception as e:
                send_error(e, "خطأ في تحديث البيانات")
                connection.rollback()
                flash("حدث خطأ أثناء تحديث البيانات\n خطأ: " + str(e), "error")
                return redirect(request.referrer)


        return redirect(url_for('profile'))
    # admin go to your own profile
    if user_role == "admin":
        return redirect(url_for('admin_profile'))
    return render_template('profile.html', current_user=current_user, user_role=user_role, cities=cities)


@app.route('/admin_profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    user_role = check_role()
    if user_role == "admin":
        with sqlite3.connect("Shopping.db") as connection:
            cursor = connection.cursor()
            # todo - keep it like this or make select without where condition then iterate using for loop???
            cursor.execute(f"""
            select * from Customers
            where role = 'customer'
            """)
            customers_num = len(cursor.fetchall())
            connection.commit()
            cursor.execute(f"""
            select * from Customers
            where role = 'admin'
            """)
            admins_num = len(cursor.fetchall())
            connection.commit()

        return render_template('admin_profile.html', current_user=current_user, user_role=user_role,
                               customers_num=customers_num, admins_num=admins_num)
    return redirect(url_for('profile'))


@app.route('/profile/orders', methods=['GET', 'POST'])
@login_required
def orders():
    user_role = check_role()
    # the admin cannot enter the customer orders page
    if user_role == "admin":
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
            send_error(e, "خطأ في تحميل الطلبات")
            connection.rollback()
            flash("حدث خطأ أثناء تحميل الطلبات,\n خطأ: " + str(e), "error")
            return redirect(request.referrer)

    # check - some parsing of each cart items, because it is as string!
    all_orders = [order[:-2] + (convert_str_to_dic(order[-2]), order[-1]) for order in orders_result]
    all_orders_dict = {status: [] for status in statuses}
    for order in orders_result:
        all_orders_dict[order[12]].append(order[:-2] + (convert_str_to_dic(order[-2]), order[-1]))
    return render_template("orders.html", user_role=user_role, all_orders=all_orders,
                           orders_num=len(all_orders), all_orders_dict=all_orders_dict)


@app.route('/admin_profile/all_customers_orders', methods=['GET', 'POST'])
@login_required
def all_customers_orders():
    user_role = check_role()
    # the customer cannot enter the admin orders page
    if user_role == "customer":
        return redirect(url_for('orders'))
    order_id = -1
    new_status = ""
    status_update = False
    new_total_amount = ""
    total_update = False

    if request.method == 'POST':
        if "order-status-update" in request.form.keys():
            status_update = True
            order_id, new_status = request.form["order-status-update"].split(",")
            order_id = int(order_id)
        elif "order-total-update" in request.form.keys():
            total_update = True
            order_id, new_total_amount = request.form["order-total-update"].split(",")
            order_id = int(order_id)

    # retrieve all the orders of all the users for the admin to handle
    with sqlite3.connect('Shopping.db') as connection:
        cursor = connection.cursor()
        try:
            if request.method == 'POST':
                if status_update:
                    cursor.execute(f"""
                    update Orders
                    set status = '{new_status}'
                    where id_number = {order_id}
                    """)
                elif total_update:
                    cursor.execute(f"""
                    update Orders
                    set total_amount = {new_total_amount}
                    where id_number = {order_id}
                    """)
                connection.commit()
            cursor.execute("""
            select * from Orders
            """)
            orders_result = cursor.fetchall()
            customer_email = orders_result[0][7]
            # todo - send email to customer when updating order status
            # send_email("mohammad.gh454@gmail.com",
            #            GMAIL_PASS,
            #            customer_email,
            #            "تم تحديث حالة الطلب",
            #            f"""
            #            تم تحديث حالة طلبك الى {new_status}\n
            #             والسعر الكلي إلى {new_total_amount}
            #             """, "plain")
            connection.commit()
        except Exception as e:
            send_error(e, "خطأ في تحميل الطلبات")
            connection.rollback()
            flash("حدث خطأ أثناء تحميل الطلبات,\n خطأ: " + str(e), "error")
            return redirect(request.referrer)
        # check - some parsing of each cart items, because it is as string!


        all_orders_dict = {status: [] for status in statuses}
        orders_count = 0
        for order in orders_result:
            orders_count += 1
            if order[0] == order_id and status_update:
                all_orders_dict[new_status].append(order[:-3] + (new_status, convert_str_to_dic(order[-2]), order[-1]))
            else:
                all_orders_dict[order[12]].append(order[:-2] + (convert_str_to_dic(order[-2]), order[-1]))

        total_delivered = 0
        for cur_order in all_orders_dict["تم التوصيل"]:
            total_delivered += cur_order[11]
    return render_template('all_customers_orders.html',
                           user_role=user_role, orders_num=orders_count,
                           statuses=statuses, all_orders_dict=all_orders_dict,
                           total_delivered=total_delivered)


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
    if STORE_CART and request.method == "POST" and user_role == "customer":
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
        img_src = [img[7:] for img in result[3].split("&")]

    return render_template('product.html', user_role=user_role, result=result, images=img_src)


@app.route('/admin_profile/handling_products', methods=['GET', 'POST'])
@login_required
def handling_products():
    user_role = check_role()
    # just the admin can go to products handling page
    if user_role == "admin":
        return render_template('handling_products.html', user_role=user_role)
    return redirect(url_for('profile'))


@app.route('/admin_profile/handling_products/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    user_role = check_role()
    # just admin can add products
    if user_role != "admin":
        return redirect(url_for('profile'))

    done = request.args.get('done')
    name = request.args.get('name')
    ptype = request.args.get('ptype')
    id_num = request.args.get('id_num')

    # we enter this if when adding product
    if request.method == "POST":
        product_name = request.form['product-name']
        product_type = request.form['product-type']
        # product_images = request.files.getlist('product-img')
        product_images = []
        i = 1
        while ('product-img' + str(i)) in request.files.keys():
            product_images.append(request.files['product-img' + str(i)])
            i += 1
        
        product_description = request.form['product-description']
        product_price = request.form['product-price']
        product_items_left = request.form['product-items-left']
        product_publish_year = "" #request.form['product-publish-year']
        product_author = " " #request.form['product-author']
        # product_categories = request.form['product-categories']
        # product_on_sale = request.form['product-on-sale']
        # product_sale_price = request.form['product-sale-price']

        # categories = [x.strip() for x in product_categories.split(',')]

        # add the entered product info to the database
        with sqlite3.connect("Shopping.db") as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO Products (name, type, price, items_left, description, publish_year, author_name) " # , categories
                    "VALUES(?, ?, ?, ?, ?, ?, ?)",
                    (product_name, product_type, product_price, product_items_left, product_description,
                     product_publish_year, product_author))
                    #  product_categories)

                # validating filename and creating img src path to store in database
                product_img = ""
                for img_file in product_images:
                    filename = secure_filename(img_file.filename)
                    product_folder = types_dict[product_type]
                    img_path = f'static/images/{product_folder}'
                    if not os.path.exists(img_path + f"/{cursor.lastrowid}"):
                        os.mkdir(img_path + f"/{cursor.lastrowid}")
                    img_path += f"/{cursor.lastrowid}/{filename}"
                    img_file.save(img_path)
                    product_img += img_path + "&"
                product_img = product_img[:-1]

                cursor.execute(f"""
                update Products
                set img_path = '{product_img}'
                where id_number = {cursor.lastrowid}
                """)

                connection.commit()
                # successfully added
                flash(f"تمت إضافة ال{product_type} بنجاح", category="success")
                return redirect(url_for('add_product', done=True, name=product_name, ptype=product_type, id_num=cursor.lastrowid))
            except Exception as e:
                send_error(e, f"حدث خطأ أثناء إضافة ال{product_type}")
                connection.rollback()
                # failed to add
                flash(f"حدث خطأ أثناء إضافة ال{product_type}" + f": {e}", category="error")
                return redirect(request.referrer)

    # if we arrive now to add product page
    return render_template('add_product.html', user_role=user_role, done=done, name=name, ptype=ptype, types=types, id_num=id_num)


@app.route('/admin_profile/handling_products/remove_product', methods=['GET', 'POST'])
@login_required
def remove_product():
    user_role = check_role()
    # just the admin can enter removing product page
    if user_role != "admin":
        return redirect(url_for('profile'))

    if request.method == "POST":
        product_id = request.form["search-product-id-input"]
        # if the user didn't enter any number to search for
        if product_id.strip() == "":
            flash("لم يتم إدخال أي رقم", "warning")
            return redirect(url_for('remove_product'))

        with sqlite3.connect("Shopping.db") as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(f"""
                    select * from Products
                    where id_number = {product_id}           
                    """)
                product_info = cursor.fetchone()
                connection.commit()

                shutil.rmtree(f"static/images/{types_dict[product_info[2]] + '/' + str(product_id)}")

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
                send_error(e, f"حدث خطأ أثناء إزالة المنتج رقم {product_id}")
                connection.rollback()
                flash(f"حدث خطأ أثناء إزالة منتج رقم {product_id}" + f": {e}", "error")
                return redirect(request.referrer)

    return render_template('remove_product.html', user_role=user_role)


@app.route('/admin_profile/handling_products/search_update_product', methods=['GET', 'POST'])
@login_required
def search_update_product():
    user_role = check_role()
    if user_role == "admin":
        return render_template("search_update_product.html", user_role=user_role)
    return redirect(url_for('profile'))


@app.route('/admin_profile/handling_products/update_product', methods=['GET', 'POST'])
@login_required
def update_product():
    user_role = check_role()
    # just the admin can enter update product page
    if user_role != "admin":
        return redirect(url_for('profile'))

    done = request.args.get('done')
    name = request.args.get('name')
    ptype = request.args.get('ptype')
    result = session.get('result')

    if request.method == "POST":
        # search for product
        if request.form.get('searched-update-id') and request.form.get('searched-update-id').strip() != "":
            id_num = int(request.form.get('searched-update-id'))
            with sqlite3.connect("Shopping.db") as connection:
                cursor = connection.cursor()
                try:
                    cursor.execute(f"""
                            select * from Products
                            where id_number = {id_num}
                            """)
                    connection.commit()
                    flash(f"تم إيجاد المنتج رقم {id_num}", "success")
                except Exception as e:
                    send_error(e, f"حدث خطأ أثناء البحث عن منتج رقم {id_num}")
                    connection.rollback()
                    flash(f"حدث خطأ أثناء البحث عن منتج رقم {id_num}" + f": {e}", "error")
                    return redirect(request.referrer)

                result = cursor.fetchone()
                session['result'] = result
                img_src = [img[7:] for img in result[3].split("&")]
            return render_template('update_product.html', user_role=user_role, done=done, result=result, name=name, types=types,
                                   ptype=ptype, images=img_src)
        # deleting image
        elif request.form.get('delete-img') and request.form.get('delete-img').strip() != "":
            tmp = request.form['delete-img'].split(',')
            id_num = int(tmp[0])
            static_index = tmp[1].index("static")
            to_delete_img = tmp[1][static_index:]
            with sqlite3.connect("Shopping.db") as connection:
                cursor = connection.cursor()
                try:
                    cursor.execute(f"""
                    select img_path from Products
                    where id_number = {id_num}
                    """)

                    result = cursor.fetchone()
                    connection.commit()
                    cur_images = result[0].split('&')
                    cur_images.remove(to_delete_img)
                    new_images = '&'.join(cur_images)

                    cursor.execute(f"""
                    update Products
                    set img_path = '{new_images}'
                    where id_number = {id_num}
                    """)

                    cursor.execute(f"""
                    select * from Products
                    where id_number = {id_num}
                    """)

                    result = cursor.fetchone()
                    session['result'] = result

                    connection.commit()
                    return redirect(url_for('update_product'))
                except Exception as e:
                    send_error(e, f"حدث خطأ أثناء إزالة الصورة")
                    connection.rollback()
                    flash("حدث خطأ أثناء إزالة الصورة\nخطأ:" + str(e), "error")
                    return redirect(request.referrer)

        # updating product
        elif request.form.get('product-id-input') is not None and request.form.get('product-id-input').strip() != "":
            product_id = request.form['product-id-input']
            product_name = request.form['product-name']
            product_type = request.form['product-type']

            product_description = request.form['product-description']
            product_price = request.form['product-price']
            product_items_left = request.form['product-items-left']

            with sqlite3.connect("Shopping.db") as connection:
                cursor = connection.cursor()
                cursor.execute(f"""
                select * from Products
                where id_number = {int(product_id)}
                """)
                cur_images = cursor.fetchone()[3] + "&"
                product_images = []
                i = cur_images.count("&") + 1
                while ('product-img' + str(i)) in request.files.keys():
                    product_images.append(request.files['product-img' + str(i)])
                    i += 1
                
                try:
                    for img_file in product_images:
                        filename = secure_filename(img_file.filename)
                        product_folder = types_dict[product_type]
                        img_path = f'static/images/{product_folder}'
                        if not os.path.exists(img_path + f"/{product_id}"):
                            os.mkdir(img_path + f"/{product_id}")
                        img_path += f"/{product_id}/{filename}"
                        img_file.save(img_path)
                        cur_images += img_path + "&"
                    cur_images = cur_images[:-1]

                    # todo - cannot change type of product
                    # type = '{product_type}',

                    cursor.execute(f"""
                    update Products
                    set name = '{product_name}',
                    img_path = '{cur_images}',
                    price = '{product_price}',
                    items_left = {product_items_left},
                    description = '{product_description}'
                    where id_number = {int(product_id)}
                    """)

                    connection.commit()
                    flash(f"تم تعديل المنتج رقم {product_id}", "success")
                except Exception as e:
                    send_error(e, f"حدث خطأ أثناء تعديل المنتج رقم {product_id}")
                    connection.rollback()
                    flash(f"حدث خطأ أثناء تعديل منتج رقم {product_id}" + f": {e}", "error")
                    return redirect(request.referrer)

                return render_template('update_product.html', done_updating=True, name=product_name, ptype=product_type,
                                       id_num=product_id)
    img_src = [img[7:] for img in result[3].split("&")]
    return render_template('update_product.html', done_updating=False, result=result, images=img_src, types=types)


@app.route('/shopping_cart', methods=['GET', 'POST'])
def shopping_cart():
    user_role = check_role()
    # prevent admin from entering the shopping cart, it is for customeeeers
    if current_user.is_authenticated and user_role == "admin":
        flash("سلة التسوق فقط للزبائن", category="warning")
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
                        # if cur_res_rows[5] > 0:
                        result[cur_id] = (int(quantity), cur_res_rows)
                        total += int(float(cur_res_rows[4])) * int(quantity)
                    except Exception as e:
                        send_error(e, f"حدث خطأ في سلة التسوق, رقم المنتج: {cur_id}")
                        connection.rollback()
                        flash(f"حدث خطأ في سلة التسوق, رقم المنتج: {cur_id} \n خطأ:" + str(e), "error")
                        return redirect(request.referrer)

                # commit when finish the loop
                connection.commit()
                session["cart-items"] = result
                session["total"] = total
                return redirect(url_for('shopping_cart'))
    # todo - remove the items with 0 quantity
    # to_remove = []
    # for id_num, value in session.get("cart-items").items():
    #     quantity, item = value
    #     if item[5] == 0:
    #         session["total"] -= quantity * item[4]
    #         to_remove.append(id_num)
    # for id_num in to_remove:
    #     session["cart-items"].pop(id_num)
    return render_template('shopping_cart.html', user_role=user_role, cart_items=session.get("cart-items"),
                           total=session.get("total") if session.get("total") else 0)


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    user_role = check_role()
    # admin go awaaaay
    if user_role == "admin":
        flash("لا يمكن للمسؤول الدخول لصفحة الدفع", "warning")
        return redirect(url_for("home"))
    
    if session.get("cart-items") == {} or session.get("total") == 0:
        flash("عليك إضافة منتجات لسلة التسوق كي تقوم بالدفع", "warning")
        return redirect(url_for("home"))

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

        role = user_role
        # تم تأكيد الطلب
        # تم تجهيز الطلب
        # تم توصيل الطلب
        status = "تم تأكيد الطلب"
        total_amount = session.get("total")
        shipping = 25
        total_amount = str(int(total_amount) + shipping)
        cart_items = session.get("cart-items")
        date_purchased = datetime.datetime.now()
        date_joined = "زبون منذ " + str(date_purchased.date())
        date_purchased = date_purchased.strftime("%Y-%m-%d %H:%M")

        password = request.form['customer-password'].strip()
        

        with sqlite3.connect("Shopping.db") as connection:
            cursor = connection.cursor()
            # register the guest customer to the website
            if user_role != "customer" and password != "":
                role = "customer"
                hashed_password = bcrypt.generate_password_hash(password)
                try:
                    cursor.execute("""
                    INSERT INTO Customers(phone_number, first_name, last_name, role, date_joined, city, address, backup_phone, password, email)
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (phone_number, first_name, last_name, role, date_joined, city, address, backup_phone,
                          hashed_password, email))

                    # todo - should I commit 2 times?
                    connection.commit()
                    # make initial cart items entry for the new customer
                    # cursor.execute(f"""
                    # insert into Cart_Items(customer_id)
                    # values({cursor.lastrowid})
                    # """)
                    # connection.commit()
                    # successfully registered
                    flash("تم التسجيل في الموقع بنجاح", category="success")
                    user = load_user(cursor.lastrowid)
                    login_user(user)
                    send_email("mohammad.gh454@gmail.com", GMAIL_PASS,
                               "m7md.gh.99@hotmail.com",
                               "تم تسحيل زبون جديد",
                               f"زبون جديد بإسم {first_name} {last_name}\n "
                               f"email: {email}\nphone: {phone_number}", "plain")
                except Exception as e:
                    send_error(e, "خطأ في التسجيل للموقع")
                    connection.rollback()
                    # failed to register
                    flash("حدث خطأ أثناء التسجيل للموقع" + f": {e}", category="error")
                    return redirect(request.referrer)

            # now add the order to the Orders table (after registering the guest customer)
            # iterate over all the cart items to store in the order info
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
                    send_error(e, f"حدث خطأ أثناء الدفع")
                    connection.rollback()
                    flash(f"حدث خطأ أثناء الدفع\nنوع الخطأ: " + str(e), "error")
                    return redirect(request.referrer)

            session["total"] = 0
            session["cart-items"] = {}

            # store the order in Orders SQL table
            if user_role == "customer":
                cursor.execute(f"""
                insert into Orders(customer_id, customer_first_name, customer_last_name, role, city, address, email, backup_phone, customer_phone_number, order_date, total_amount, status, cart_items)
                values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (current_user.id_number, first_name, last_name, role, city, address, email, backup_phone, phone_number,
                    date_purchased, total_amount, status, str(cart_items)))
            #  guest
            else:
                # delete - i think... because we will force guest to register to website
                cursor.execute(f"""
                insert into Orders(customer_first_name, customer_last_name, role, city, address, email, backup_phone, customer_phone_number, order_date, total_amount, status, cart_items)
                values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                , (first_name, last_name, role, city, address, email, backup_phone, phone_number, date_purchased, total_amount, status, str(cart_items)))
            
            connection.commit()
            send_email("mohammad.gh454@gmail.com", GMAIL_PASS,
                       "m7md.gh.99@hotmail.com",
                       f"طلب جديد برقم {cursor.lastrowid}",
                       f"طلب جديد برقم {cursor.lastrowid}\nللزبون {first_name} {last_name}\n"
                       f" email: {email}\n"
                       f"phone: {phone_number}", "plain")
        return render_template("order_approved.html", user_role=user_role)

    cur_user = current_user if user_role != "guest" else None
    return render_template('checkout.html', cities=cities, user_role=user_role, total=total, cur_user=cur_user)


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


@app.route('/admin_profile/all_customers', methods=['GET', 'POST'])
@login_required
def all_customers():
    user_role = check_role()
    if user_role != "admin":
        return redirect(request.referrer)

    with sqlite3.connect("Shopping.db") as connection:
        cursor = connection.cursor()
        cursor.execute("select * from Customers")

        users = cursor.fetchall()
        connection.commit()

    return render_template("all_customers.html", users=users, user_role=user_role, users_num=len(users))


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
            tup = value[:indx].strip(), value[indx + 1:].strip()
            for j, v in enumerate(tup[1][1:-1].split(",")):
                if j == 0 or j == 5:
                    item.append(int(v.strip()))
                else:
                    item.append(v.strip())

            value = int(tup[0]), tuple(item)
            values.append(value)

    dic = {keys[i]: values[i] for i in range(len(keys))}
    return dic


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


if __name__ == "__main__":
    # app.run(host="0.0.0.0", debug=True)
    app.run()

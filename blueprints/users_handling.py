import random
import sqlite3
import datetime
import string

from helpers import check_role, send_error, send_email, GMAIL_PASS, cities, User, WEBSITE_EMAIL
from flask_login import current_user, login_required, logout_user, login_user
from flask import flash, request, redirect, url_for, render_template, Blueprint
from extensions import bcrypt, login_manager


user_bp = Blueprint('users', __name__)


@login_manager.user_loader
def load_user(user_id):
    # this function to load user using its id number
    with sqlite3.connect("Shopping.db") as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(f"""
            select *
            from Users
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


@user_bp.route('/login', methods=['POST', 'GET'])
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
                    from Users
                    where phone_number = '{phone_number}'
                    """
            else:
                # retrieve the user that has this email
                check_user_existence = f"""
                    select *
                    from Users
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
                    return redirect(url_for('admin.admin_profile'))
                return redirect(url_for('profile.profile'))
            else:
                flash("خطأ في إحدى الخانات (رقم الهاتف/البريد الإلكتروني أو كلمة المرور) الرجاء المحاولة مرة أخرى", "warning")
                return redirect(request.referrer)
        # if there is no user has these unique info, then go and register the new user
        elif len(res_rows) == 0:
            flash("لم تقم بالتسجيل في الموقع من قبل, تفضّل بالتسجيل في الموقع", category="warning")
            return redirect(url_for('users.register'))
        # if we found more than one user with the same info
        else:
            flash("حدث خطأ أثناء تسجيل الدخول (هنالك أكثر من مستخدم لديهم نفس رقم الهاتف أو البريد الإلكتروني)", "error")
            return redirect(url_for('users.login'))

    # if the current user is already logged in, then go to profile
    if current_user.is_authenticated:
        if user_role == "admin":
            return redirect(url_for('admin.admin_profile'))
        return redirect(url_for('profile.profile'))

    return render_template('login.html', user_role=user_role)


@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    user_role = check_role()
    # registered users cannot register while they are logged in
    if user_role != "guest":
        return redirect(url_for('profile.profile'))

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
        if phone_number in ["0543818223", "0528942919"]:
            role = "admin"
        email = form['customer-email'].strip()
        backup_phone = form['customer-backup-phone'].strip()
        password = form['customer-password'].strip()
        hashed_password = bcrypt.generate_password_hash(password)

        with sqlite3.connect("Shopping.db") as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                INSERT INTO Users(phone_number, first_name, last_name, 
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
                print(WEBSITE_EMAIL)
                print(GMAIL_PASS)
                send_email(WEBSITE_EMAIL, GMAIL_PASS, WEBSITE_EMAIL,
                           "تم تسحيل زبون جديد",
                           f"""
                           زبون جديد بإسم {first_name} {last_name}\n
                           email: {email}\n
                           phone: {phone_number}
                            """, "plain")
                return redirect(url_for('profile.profile'))
            except Exception as e:
                send_error(e, "خطأ في التسجيل للموقع")
                connection.rollback()
                # failed to register
                flash("حدث خطأ أثناء التسجيل للموقع" + f": {e}", category="error")
                return redirect(request.referrer)

    user_role = check_role()
    return render_template('register.html', cities=cities, user_role=user_role)


@user_bp.route('/forgot_password', methods=['POST', 'GET'])
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
                    select * from Users
                    where phone_number = '{customer_phone}'
                    """)
                    wanted_user = cursor.fetchone()
                    user_fullname = wanted_user[2] + " " + wanted_user[3]
                    temp_password = bcrypt.generate_password_hash(unique_token).decode('utf-8')
                    cursor.execute(f"""
                    update Users
                    set password = '{temp_password}',
                    forgot_password = 1
                    where phone_number = '{customer_phone}'
                    """)
                    customer_email = wanted_user[10]
                else:
                    cursor.execute(f"""
                    select * from Users
                    where email = '{customer_email}'
                    """)
                    wanted_user = cursor.fetchone()
                    user_fullname = wanted_user[2] + " " + wanted_user[3]
                    cursor.execute(f"""
                    update Users
                    set password = '{bcrypt.generate_password_hash(unique_token)}',
                    forgot_password = 1
                    where email = '{customer_email}'
                    """)
                connection.commit()
                send_email(WEBSITE_EMAIL, GMAIL_PASS,
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
                return redirect(url_for('users.login'))
            except Exception as e:
                send_error(e, "خطأ في استعادة كلمة المرور")
                connection.rollback()
                flash("حدث خطأ أثناء استعادة كلمة المرور\n خطأ: " + str(e), "error")
                return redirect(request.referrer)
    return render_template('forgot_password.html')


@user_bp.route('/new_password', methods=['POST', 'GET'])
def new_password():
    if check_role() != "guest":
        flash("يجب تسجيل الخروج أولاً", "warning")
        return redirect(url_for('profile.profile'))
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
                update Users
                set password = '{new_hashed_password}',
                forgot_password = 0
                where phone_number = '{phone_number}'
                """)
                connection.commit()
                flash("تم تغيير كلمة المرور بنجاح", "success")
                return redirect(url_for('users.login'))
            except Exception as e:
                send_error(e, "خطأ في تغيير كلمة المرور")
                connection.rollback()
                flash("حدث خطأ أثناء تغيير كلمة المرور\n خطأ: " + str(e), "error")
                return redirect(request.referrer)
    return render_template('new_password.html')


@user_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('users.login'))

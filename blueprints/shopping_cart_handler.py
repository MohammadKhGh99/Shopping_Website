import sqlite3
import datetime

from helpers import check_role, send_error, send_email, GMAIL_PASS, cities, User
from flask import flash, request, render_template, redirect, url_for, session, Blueprint
from flask_login import current_user, login_user
from extensions import bcrypt, login_manager


shopping_cart_bp = Blueprint('shopping_cart', __name__)


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


@shopping_cart_bp.route('/', methods=['GET', 'POST'])
def shopping_cart():
    user_role = check_role()
    # prevent admin from entering the shopping cart, it is for customeeeers
    if current_user.is_authenticated and user_role == "admin":
        flash("سلة التسوق فقط للزبائن", category="warning")
        return redirect(url_for('admin.admin_profile'))

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
                return redirect(url_for('shopping_cart.shopping_cart'))
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


@shopping_cart_bp.route('/checkout', methods=['GET', 'POST'])
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

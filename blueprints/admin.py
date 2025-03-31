import sqlite3

from helpers import check_role, send_error, statuses, convert_str_to_dic
from flask import render_template, redirect, url_for, request, flash, Blueprint
from flask_login import login_required, current_user


admin_bp = Blueprint('admin', __name__, url_prefix='/admin_profile')


@admin_bp.route('/', methods=['GET', 'POST'])
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
    return redirect(url_for('profile.profile'))


@admin_bp.route('/all_customers_orders', methods=['GET', 'POST'])
@login_required
def all_customers_orders():
    user_role = check_role()
    # the customer cannot enter the admin orders page
    if user_role == "customer":
        return redirect(url_for('profile.orders'))
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


@admin_bp.route('/all_customers', methods=['GET', 'POST'])
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

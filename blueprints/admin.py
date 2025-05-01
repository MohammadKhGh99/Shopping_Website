import sqlite3
import datetime
import os
import shutil
import json

from helpers import check_role, send_error, statuses, convert_str_to_dic, DB_FILE, send_email, GMAIL_PASS, WEBSITE_EMAIL, update_last_backup_time_in_file, get_last_backup_time_from_file
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
            select * from Users
            where role = 'customer'
            """)
            Users_num = len(cursor.fetchall())
            connection.commit()
            cursor.execute(f"""
            select * from Users
            where role = 'admin'
            """)
            admins_num = len(cursor.fetchall())
            connection.commit()

        # get the last backup time from the txt file
        last_backup_time = get_last_backup_time_from_file()

        return render_template('admin_profile.html', current_user=current_user, user_role=user_role,
                               Users_num=Users_num, admins_num=admins_num, last_backup_time=last_backup_time)
    return redirect(url_for('profile.profile'))


@admin_bp.route('/all_Users_orders', methods=['GET', 'POST'])
@login_required
def all_Users_orders():
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
            # send_email(WEBISTE_EMAIL,
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
    return render_template('all_Users_orders.html',
                           user_role=user_role, orders_num=orders_count,
                           statuses=statuses, all_orders_dict=all_orders_dict,
                           total_delivered=total_delivered)


@admin_bp.route('/all_Users', methods=['GET', 'POST'])
@login_required
def all_Users():
    user_role = check_role()
    if user_role != "admin":
        return redirect(request.referrer)

    with sqlite3.connect("Shopping.db") as connection:
        cursor = connection.cursor()
        cursor.execute("select * from Users")

        users = cursor.fetchall()
        connection.commit()

    return render_template("all_Users.html", users=users, user_role=user_role, users_num=len(users))


@admin_bp.route('/backup', methods=['POST'])
@login_required
def backup():
    user_role = check_role()
    if user_role != "admin":
        return redirect(request.referrer)

    now = datetime.datetime.now()
    backup_filename = f"{os.path.splitext(DB_FILE)[0]}_backup_{now.strftime('%Y%m%d_%H%M%S')}.db"

    # Copy the database file
    shutil.copy2(DB_FILE, backup_filename)

    send_email(WEBSITE_EMAIL, 
               GMAIL_PASS,
               WEBSITE_EMAIL,
               "نسخة احتياطية من قاعدة البيانات",
               f"تم أخذ نسخة احتياطية من قاعدة البيانات في {now.strftime('%Y-%m-%d %H:%M:%S')}\n",
               "plain",
               backup_filename)
    
    # Update the last backup time in the JSON file
    update_last_backup_time_in_file()

    print(f"Backup created: {backup_filename}")
    os.remove(backup_filename)
    flash("تم أخذ نسخة احتياطية من قاعدة البيانات بنجاح", "success")
    return redirect(request.referrer)
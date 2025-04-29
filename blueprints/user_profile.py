import sqlite3

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from helpers import check_role, send_error, convert_str_to_dic, cities, statuses


user_profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@user_profile_bp.route('/', methods=['GET', 'POST'])
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
                update Users
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
                return redirect(url_for('profile.profile'))
            except Exception as e:
                send_error(e, "خطأ في تحديث البيانات")
                connection.rollback()
                flash("حدث خطأ أثناء تحديث البيانات\n خطأ: " + str(e), "error")
                return redirect(request.referrer)


        return redirect(url_for('profile.profile'))
    # admin go to your own profile
    if user_role == "admin":
        return redirect(url_for('admin.admin_profile'))
    return render_template('profile.html', current_user=current_user, user_role=user_role, cities=cities)


@user_profile_bp.route('/orders', methods=['GET', 'POST'])
@login_required
def orders():
    user_role = check_role()
    # the admin cannot enter the customer orders page
    if user_role == "admin":
        return redirect(url_for('admin.all_Users_orders'))

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
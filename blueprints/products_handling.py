import sqlite3
import shutil
import os

from helpers import check_role, send_error, r2_handler, R2_DEV_BUCKET_URL
from flask import render_template, redirect, url_for, request, flash, session, Blueprint
from flask_login import login_required
from werkzeug.utils import secure_filename


products_handling_bp = Blueprint('products_handling', __name__)

types_dict = {"كتب": "books", "أزياء": "clothes", "ركن الهدايا": "gifts_corner"}
types = ["كتب", "أزياء", "ركن الهدايا"]


@products_handling_bp.errorhandler(Exception)
def handle_exception(e):
    # Handle the exception and log it
    send_error(e, "خطأ غير متوقع")
    # TODO: redirect to a custom error page or show a message
    return redirect(request.referrer)


@products_handling_bp.route('/admin_profile/handling_products', methods=['GET', 'POST'])
@login_required
def handling_products():
    user_role = check_role()
    # just the admin can go to products handling page
    if user_role == "admin":
        return render_template('handling_products.html', user_role=user_role)
    return redirect(url_for('products_handling.profile.profile'))


@products_handling_bp.route('/admin_profile/handling_products/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    user_role = check_role()
    # just admin can add products
    if user_role != "admin":
        return redirect(url_for('products_handling.profile.profile'))

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

                # # validating filename and creating img src path to store in database
                # product_img = ""
                # for img_file in product_images:
                #     filename = secure_filename(img_file.filename)
                #     product_folder = types_dict[product_type]
                #     img_path = f'static/images/{product_folder}'
                #     if not os.path.exists(img_path + f"/{cursor.lastrowid}"):
                #         os.mkdir(img_path + f"/{cursor.lastrowid}")
                #     img_path += f"/{cursor.lastrowid}/{filename}"
                #     img_file.save(img_path)
                #     product_img += img_path + "&"
                # product_img = product_img[:-1]

                # cursor.execute(f"""
                # update Products
                # set img_path = '{product_img}'
                # where id_number = {cursor.lastrowid}
                # """)

                # Upload images to Cloudflare R2 and store their URLs
                product_img_urls = ""
                for img_file in product_images:
                    filename = secure_filename(img_file.filename)
                    object_name = f"{product_type}/{cursor.lastrowid}/{filename}"
                    
                    uploaded_url = r2_handler.upload_image(img_file, object_name)
                    if uploaded_url:
                        product_img_urls += R2_DEV_BUCKET_URL + "/" + object_name + "&"
                    else:
                        raise Exception("Failed to upload image to Cloudflare R2.")

                product_img_urls = product_img_urls[:-1]  # Remove trailing '&'
                # Update the product record with image URLs
                cursor.execute(f"""
                UPDATE Products
                SET img_path = '{product_img_urls}'
                WHERE id_number = {cursor.lastrowid}
                """)


                connection.commit()
                # successfully added
                flash(f"تمت إضافة ال{product_type} بنجاح", category="success")
                return redirect(url_for('products_handling.add_product', done=True, name=product_name, ptype=product_type, id_num=cursor.lastrowid))
            except Exception as e:
                send_error(e, f"حدث خطأ أثناء إضافة ال{product_type}")
                connection.rollback()
                # failed to add
                flash(f"حدث خطأ أثناء إضافة ال{product_type}" + f": {e}", category="error")
                return redirect(request.referrer)

    # if we arrive now to add product page
    return render_template('add_product.html', user_role=user_role, done=done, name=name, ptype=ptype, types=types, id_num=id_num)


@products_handling_bp.route('/admin_profile/handling_products/remove_product', methods=['GET', 'POST'])
@login_required
def remove_product():
    user_role = check_role()
    # just the admin can enter removing product page
    if user_role != "admin":
        return redirect(url_for('products_handling.profile.profile'))

    if request.method == "POST":
        product_id = request.form["search-product-id-input"]
        # if the user didn't enter any number to search for
        if product_id.strip() == "":
            flash("لم يتم إدخال أي رقم", "warning")
            return redirect(url_for('products_handling.admin_profile.handling_products.remove_product'))

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
                return redirect(url_for('products_handling.admin_profile.handling_products.remove_product'))
            except Exception as e:
                send_error(e, f"حدث خطأ أثناء إزالة المنتج رقم {product_id}")
                connection.rollback()
                flash(f"حدث خطأ أثناء إزالة منتج رقم {product_id}" + f": {e}", "error")
                return redirect(request.referrer)

    return render_template('remove_product.html', user_role=user_role)


@products_handling_bp.route('/admin_profile/handling_products/search_update_product', methods=['GET', 'POST'])
@login_required
def search_update_product():
    user_role = check_role()
    if user_role == "admin":
        return render_template("search_update_product.html", user_role=user_role)
    return redirect(url_for('products_handling.profile.profile'))


@products_handling_bp.route('/admin_profile/handling_products/update_product', methods=['GET', 'POST'])
@login_required
def update_product():
    user_role = check_role()
    # just the admin can enter update product page
    if user_role != "admin":
        return redirect(url_for('products_handling.profile.profile'))

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
                    result = cursor.fetchone()
                    if result is None:
                        flash(f"لم يتم إيجاد منتج رقم {id_num}", "warning")
                        return redirect(url_for('products_handling.search_update_product'))
                    flash(f"تم إيجاد المنتج رقم {id_num}", "success")
                except Exception as e:
                    send_error(e, f"حدث خطأ أثناء البحث عن منتج رقم {id_num}")
                    connection.rollback()
                    flash(f"حدث خطأ أثناء البحث عن منتج رقم {id_num}" + f": {e}", "error")
                    return redirect(request.referrer)

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
                    return redirect(url_for('products_handling.admin_profile.handling_products.update_product'))
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
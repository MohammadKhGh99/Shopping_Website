import os
import sqlite3
from flask import render_template, Flask, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'lakjfpoek[gf;sldg165478'
app.config['DEBUG'] = True


books_lst = [filename for filename in os.listdir('static/images/books')] * 4
clothes_lst = [filename for filename in os.listdir('static/images/clothes')] * 4

with open("static/Books_Authors.txt", encoding="utf8") as f:
    authors = f.readlines()
with open("static/Books_Dates.txt", encoding="utf8") as f:
    publishes = f.readlines()
with open("static/Books_Publishers.txt", encoding="utf8") as f:
    publishers = f.readlines()
# with open("static/Books_Others.txt", encoding="utf8") as f:
#     other = f.readlines()
    

@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/books')
def books():
    return render_template('books.html', products=books_lst, authors=authors, publishes=publishes, publishers=publishers)#, other=other)


@app.route('/product')
def product():
    return render_template('product.html')


@app.route('/clothes')
def clothes():
    return render_template('clothes.html', products=clothes_lst)


@app.route('/sign_in')
def sign_in():
    return render_template('sign_in.html')


@app.route('/sign_up')
def sign_up():
    return render_template('sign_up.html')


@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact_us')
def contact_us():
    return render_template('contact_us.html')


@app.route('/shopping_cart')
def shopping_cart():
    return render_template('shopping_cart.html')




@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404


if __name__ == "__main__":
    # webbrowser.open("http://127.0.0.1:5000/home")
    # app.run()
    app.run(host="0.0.0.0")
    
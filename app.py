import os
import webbrowser

from jinja2 import Environment
from flask import render_template, Flask, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'lakjfpoek[gf;sldg165478'
app.config['DEBUG'] = True
# env = Environment()
# env.filters['increment'] = lambda value: value + 1

products = [filename for filename in os.listdir('static/images/products')] * 4
# authors = []
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
    return render_template('home.html', products=products, authors=authors, publishes=publishes, publishers=publishers)#, other=other)


@app.route('/sign_in')
def sign_in():
    return render_template('sign_in.html')


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
    webbrowser.open("http://127.0.0.1:5000/home")
    app.run()
    
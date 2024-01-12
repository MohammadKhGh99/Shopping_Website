import os
import webbrowser

from flask import render_template, Flask, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'lakjfpoek[gf;sldg165478'
app.config['DEBUG'] = True

products = [filename for filename in os.listdir('static/images/products')] * 4


@app.route('/home')
def home():
    return render_template('home.html', products=products)


@app.route('/sign_in')
def sign_in():
    return render_template('sign_in.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404








if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000/home")
    app.run()
    
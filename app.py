import sqlite3
from flask import Flask, render_template, request, Response, redirect, url_for, flash, session
import re
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import text
from werkzeug.security import generate_password_hash

app = Flask(__name__)

def db():
    connect = sqlite3.connect('database.db')
    connect.execute('''CREATE TABLE IF NOT EXISTS users (
                            username TEXT NOT NULL,
                            email TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL)''')

    

@app.route('/', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect("database.db") as users:
            cursor = users.cursor()
            cursor.execute("INSERT INTO users \
                        (username, email, password) VALUES (?,?,?)",
                        (username, email, password))
            users.commit()

        return render_template("index.html") 
    else: 
        return render_template('register.html') 
        

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    
    labels = ["Dog","Cat","Rabbit","Mouse"]
    values =[3,2,5,6]

   
    return render_template("home.html",labels=labels,values=values)

@app.route('/logout')
def logout():
    return render_template("logout.html")

@app.route('/database')
def database():
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    cursor.execute('SELECT * FROM users')

    data = cursor.fetchall()
    return render_template("database.html", data=data)

@app.route('/speedtest')
def speedtest():
    return render_template('speedtest.html')

@app.route('/networks')
def networks():
    return render_template('networks.html')

@app.route('/bandwidth')
def bandwidth():
    return render_template('bandwidth.html')
@app.route('/networkHealth')
def networkHealth():
    return render_template('networkHealth.html')
@app.route('/vulnerabilites')
def vulnerabilites():
    return render_template('vulnerabilties.html')
if __name__=='__main__':
    app.run(debug = True)
import sqlite3
from flask import Flask, render_template, request, Response, redirect, url_for, flash, session
import re
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import text
import speedtest
import threading
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash
from src.broadbandtests import bandwidth_tests #imports class


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/about')
def about():
    return render_template("about.html")
def db():
    connect = sqlite3.connect('database.db')
    connect.execute('''CREATE TABLE IF NOT EXISTS users (
                            username TEXT NOT NULL,
                            email TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL)''')
    
    ##connect2 = sqlite3.connect('database.db')
    ##connect2.execute('''CREATE TABLE IF NOT EXISTS alerts (Timestamp TIMESTAMP, device TEXT not null )''')

    

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
    
   

   
    return render_template("home.html")

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

#starts the tests when the app starts
speed_test = bandwidth_tests(socketio) #creates object passing socketio through
speed_test.start_speedtests()

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
@app.route('/settingsHome')
def settingsHome():
    return render_template('settingsHome.html')
@app.route('/changeUsername',methods=['GET', 'POST'])

def changeUsername():
  
    username = request.form['username']
    newUsername =request.form['newUsername']

    with sqlite3.connect("database.db") as users:
        cursor = users.cursor()
        cursor.execute("UPDATE users  SET username =  (?) WHERE username = (?)",
                    (username,newUsername))
        users.commit()

    return render_template('changeUsername.html')
@app.route('/changePassword',methods=['GET', 'POST'])
def changePassword():
    username = request.form['username']
    password = request.form['password']
    newPassword =request.form['newPassword']

    with sqlite3.connect("database.db") as users:
        cursor = users.cursor()
        cursor.execute("UPDATE users  SET password =  (?) WHERE username = (?) AND password = (?)",
                    (newPassword,username,password))
        users.commit()
    return render_template('changePassword.html')
@app.route('/changeEmail')
def changeEmail():
    username = request.form['username']
    email = request.form['email']
    newEmail =request.form['newEmail']

    with sqlite3.connect("database.db") as users:
        cursor = users.cursor()
        cursor.execute("UPDATE users  SET email =  (?) WHERE username = (?) AND email = (?)",
                    (newEmail,username,email))
        users.commit()
    return render_template('changeEmail.html',methods=['GET', 'POST'])
@app.route('/alerts')
def alerts():
    return render_template('alerts.html')
@app.route('/vulnerabilities')
def vulnerabilities():
    return render_template('vulnerabilities.html')
if __name__=='__main__':
    
    socketio.run(app)
    
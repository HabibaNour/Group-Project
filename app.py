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
from src.SSID import selecting_SSID
#from src.finddevices import devices #fixing error, will upload on sat.
from functools import wraps 

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

ssid_selector = selecting_SSID(socketio)
#find_devices = devices(socketio)
#find_devices.handle_socket()

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/about')
def about():
    return render_template("about.html")
def db():
    connect = sqlite3.connect('database.db')
    connect.execute('''CREATE TABLE IF NOT EXISTS users (
                            username TEXT PRIMARY KEY NOT NULL,
                            email TEXT  NOT NULL,
                            password TEXT NOT NULL,
                            confpassword TEXT NOT NULL)''')
                            
    connect.commit()
    connect.close()
db()
    
    ##connect2 = sqlite3.connect('database.db')
    ##connect2.execute('''CREATE TABLE IF NOT EXISTS alerts (Timestamp TIMESTAMP, device TEXT not null )''')

    

@app.route('/', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def register():
    min_length = 8
    uppercase_regex = re.compile(r'[A-Z]')
    lowercase_regex = re.compile(r'[a-z]')
    digit_regex = re.compile(r'\d')
    special_char_regex = re.compile(r'[!@#$%^&*()_+{}[\]:;<>,.?~\\/-]')

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confpassword = request.form['confpassword']

        #add users to the database
        #check of the username is in the database with an error message
        with sqlite3.connect("database.db") as users:
            cursor = users.cursor()

            if password != confpassword:
                error="your password and confirmed password need to be the same"
                return render_template('register.html', error=error) 
            
            if len(password) < min_length:
                LenError="Weak: password should be at least 8 characters"
                return render_template('register.html', error=LenError)
            
            elif not uppercase_regex.search(password) or not lowercase_regex.search(password):
                caseError= "Weak: password should contain at least one upper and lower cases letter"
                return render_template('register.html', error=caseError)

            elif not digit_regex.search(password):
                digitError= "Weak: password should contain at least one number"
                return render_template('register.html', error=digitError)

                        
            elif not special_char_regex.search(password):
                charError= "Weak: password should contain at least one special character"
                return render_template('register.html', error=charError)


            cursor.execute("INSERT INTO users \
                        (username, email, password, confpassword) VALUES (?,?,?,?)",
                        (username, email, password, confpassword))
            users.commit()


        return redirect("/index") 
    else: 
        return render_template('register.html') 
        

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        connect = sqlite3.connect('database.db')
        connect.row_factory = sqlite3.Row
        cursor = connect.cursor()

        cursor.execute('SELECT username FROM users WHERE username = ? AND password = ?',
                        (username, password))
        user = cursor.fetchone()

        if user:
            return render_template('index.html')
        else:
            error = 'please try again'
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/logout')
def logout():
    return render_template("logout.html")

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/loginAdmin', methods=['GET', 'POST'])
def loginAdmin():
        username = 'NRHadmins' 
        password = 'NRHpassAdmins'
        
        if request.method == 'POST':
            connect = sqlite3.connect('database.db')
            cursor = connect.cursor()
            cursor.execute('SELECT * FROM users')

            data = cursor.fetchall()

            if username == username and password == password:
                return render_template('database.html', data=data)
            else:
                error = 'invalid, please try again'
                return render_template('loginAdmin.html', error=error)
            
        return render_template('loginAdmin.html')


#starts the tests when the app starts
speed_test = bandwidth_tests(socketio) #creates object passing socketio through
speed_test.start_speedtests()

@app.route('/speedtest')
def speedtest():
    return render_template('speedtest.html')

@app.route('/networks')
def networks():
    ssid_selector.start_SSID_selection()
    return render_template('networks.html')

@app.route('/test')
def test():
    return render_template('test.html') #for testing

@socketio.on('disconnect')
def handle_disconnect():
    ssid_selector.stop_SSID_selection()

@app.route('/devices')
def clients():
    return render_template('devices.html')

@app.route('/bandwidth')
def bandwidth():
    return render_template('bandwidth.html')
@app.route('/networkHealth')
def networkHealth():
    return render_template('networkHealth.html')
#settings and changing user info 
@app.route('/settingsHome')
def settingsHome():
    return render_template('settingsHome.html')

@app.route('/changePassword', methods=['GET', 'POST'])
def changePassword():
    if request.method == 'POST':
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
    if request.method == 'POST':
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
    

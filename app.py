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
from src.finddevices import devices #fixing error, will upload on sat.
from functools import wraps 
from flask_bcrypt import Bcrypt


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
app.secret_key = "groupProject"

bcrypt = Bcrypt(app)


ssid_selector = selecting_SSID(socketio)
find_devices = devices(socketio)
find_devices.handle_socket()

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
                            email TEXT NOT NULL,
                            password TEXT NOT NULL,
                            confpassword TEXT NOT NULL)''')
    
    connect.execute('''CREATE TABLE IF NOT EXISTS admins (
                            username TEXT PRIMARY KEY NOT NULL,
                            password TEXT NOT NULL)''')                            
    connect.commit()
    connect.close()
    
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

        #check if the username is in the database with an error message
        connect = sqlite3.connect('database.db')
        connect.row_factory = sqlite3.Row
        cursor = connect.cursor()

        cursor.execute('SELECT username FROM users WHERE username = ?',[username])
        userCheck = cursor.fetchone()

        cursor.execute('SELECT email FROM users WHERE email = ?',[email])
        emailCheck = cursor.fetchone()

        if userCheck:
                userError = "This username is taken, please try a different username"
                return render_template('register.html', error=userError)
        
        elif emailCheck:
            emailError = "This email is registered before, please login"
            return render_template('register.html', error=emailError)

        #insert users to the database
        with sqlite3.connect("database.db") as users:
            cursor = users.cursor()

            hash_password = bcrypt.generate_password_hash(password).decode('utf-8')
            bcrypt.generate_password_hash(hash_password)
            

            if password != confpassword:
                error="Your password and confirmed password need to be the same"
                return render_template('register.html', error=error) 
            
            if len(password ) < min_length:
                LenError="Weak: password should be at least 8 characters"
                return render_template('register.html', error=LenError)
            
            elif not uppercase_regex.search(password ) or not lowercase_regex.search(password ):
                caseError= "Weak: password should contain at least one upper and lower cases letter"
                return render_template('register.html', error=caseError)

            elif not digit_regex.search(password ):
                digitError= "Weak: password should contain at least one number"
                return render_template('register.html', error=digitError)

                        
            elif not special_char_regex.search(password ):
                charError= "Weak: password should contain at least one special character"
                return render_template('register.html', error=charError)


            cursor.execute("INSERT INTO users \
                        (username, email, password, confpassword) VALUES (?,?,?,?)",
                        (username, email, hash_password, hash_password))
            users.commit()

        return redirect("/index") 
    else: 
        return render_template('register.html') 
     
def requiredLogin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next = request.url))
        
        return f(*args,**kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

    
        connect = sqlite3.connect('database.db')
        connect.row_factory = sqlite3.Row
        cursor = connect.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?',[username])
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['username']= user['username']
            return redirect("/home")
        else:
            error = 'please try again'
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/home')
@requiredLogin
def home():
    ssid_selector.start_SSID_selection()
    return render_template("home.html")

@app.route('/logout')
def logout():
    session.clear()
    return render_template("logout.html")

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/loginAdmin', methods=['GET', 'POST'])
def loginAdmin():
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            connect = sqlite3.connect('database.db')
            connect.row_factory = sqlite3.Row
            cursor2 = connect.cursor()

            cursor2.execute('SELECT username FROM admins WHERE username = ? AND password = ?',
                            (username, password))
            admin = cursor2.fetchone()

            if admin:
                connect = sqlite3.connect('database.db')
                cursor = connect.cursor()
                cursor2 = connect.cursor()

                cursor.execute('SELECT * FROM users')
                cursor2.execute('SELECT * FROM admins')

                data = cursor.fetchall()
                data2 = cursor2.fetchall()

                return render_template('database.html', data=data, data2=data2)
            else:
                error = 'invalid, please try again'
                return render_template('loginAdmin.html', error=error)
            
        return render_template('loginAdmin.html')



#starts the tests when the app starts
speed_test = bandwidth_tests(socketio) #creates object passing socketio through
speed_test.start_speedtests()

@app.route('/speedtest')
@requiredLogin
def speedtest():
    return render_template('speedtest.html')

@app.route('/networks')
@requiredLogin
def networks():
    return render_template('networks.html')

@app.route('/devices')
@requiredLogin
def devices():
    return render_template('devices.html')

@socketio.on('disconnect')
def handle_disconnect():
    ssid_selector.stop_SSID_selection()

@app.route('/devices')
@requiredLogin
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
@requiredLogin
def settingsHome():
    return render_template('settingsHome.html')

@app.route('/changePassword', methods=['GET', 'POST'])
@requiredLogin
def changePassword():
    min_length = 8
    uppercase_regex = re.compile(r'[A-Z]')
    lowercase_regex = re.compile(r'[a-z]')
    digit_regex = re.compile(r'\d')
    special_char_regex = re.compile(r'[!@#$%^&*()_+{}[\]:;<>,.?~\\/-]')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        newPassword =request.form['newPassword']
        confpassword = request.form['confpassword']


        with sqlite3.connect("database.db") as users:
            cursor = users.cursor()
            cursor.execute("UPDATE users  SET password =  (?), confpassword = (?) WHERE username = (?) AND password = (?)",
                        (newPassword,confpassword,username, password))
            if newPassword != confpassword:
                error="your password and confirmed password need to be the same"
                return render_template('changePassword.html', error=error) 
            
            if len(newPassword) < min_length:
                LenError="Weak: password should be at least 8 characters"
                return render_template('changePassword.html', error=LenError)
            
            elif not uppercase_regex.search(newPassword) or not lowercase_regex.search(newPassword):
                caseError= "Weak: password should contain at least one upper and lower cases letter"
                return render_template('changePassword.html', error=caseError)

            elif not digit_regex.search(newPassword):
                digitError= "Weak: password should contain at least one number"
                return render_template('changePassword.html', error=digitError)

                        
            elif not special_char_regex.search(newPassword):
                charError= "Weak: password should contain at least one special character"
                return render_template('changePassword.html', error=charError)
            users.commit()
    return render_template('changePassword.html')
@app.route('/changeEmail',methods=['GET', 'POST'])
@requiredLogin
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
@requiredLogin
def alerts():
    return render_template('alerts.html')
@app.route('/vulnerabilities')
@requiredLogin
def vulnerabilities():
    return render_template('vulnerabilities.html')
if __name__=='__main__':
    
    socketio.run(app)
    

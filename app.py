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
from src.finddevices import devices 
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
                            adminUsername TEXT PRIMARY KEY NOT NULL,
                            adminEmail TEXT NOT NULL,
                            adminPassword TEXT NOT NULL,
                            adminConfPassword TEXT NOT NULL)''')                           
    connect.commit()
    connect.close()
    

    
@app.route('/', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def register():
        #source from: https://medium.com/@amaltomparakkaden/building-a-password-generator-and-strength-checker-with-flask-and-html-e8b18374d397
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

            #source for hashing: https://www.geeksforgeeks.org/password-hashing-with-bcrypt-in-flask/
            hash_password = bcrypt.generate_password_hash(password).decode('utf-8')
            bcrypt.generate_password_hash(hash_password)
            

            if password != confpassword:
                error="Your password and confirmed password need to be the same"
                return render_template('register.html', error=error) 

             #source from: https://medium.com/@amaltomparakkaden/building-a-password-generator-and-strength-checker-with-flask-and-html-e8b18374d397
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


            #source from: https://www.geeksforgeeks.org/how-to-build-a-web-app-using-flask-and-sqlite-in-python/
            cursor.execute("INSERT INTO users \
                        (username, email, password, confpassword) VALUES (?,?,?,?)",
                        (username, email, hash_password, hash_password))
            users.commit()

        return redirect("/index") 
    else: 
        return render_template('register.html') 
#source: https://flask.palletsprojects.com/en/stable/patterns/viewdecorators/
 # will lock pages so need to be logged in    
def requiredLogin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next = request.url))
        
        return f(*args,**kwargs)
    return decorated_function

#source https://flask.palletsprojects.com/en/stable/patterns/viewdecorators/
def adminLock(g):
    @wraps(g)
    def decorated_function(*args, **kwargs):
        
        if 'username' not in session:
            return redirect(url_for('index', next = request.url))
        elif 'username' in session:
            return redirect(url_for('home', next = request.url))
        
        
        return g(*args,**kwargs)
    return decorated_function
@app.route('/login', methods=['GET', 'POST'])
def login():
    #source from: https://www.digitalocean.com/community/tutorials/how-to-use-an-sqlite-database-in-a-flask-application
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

    
        connect = sqlite3.connect('database.db')
        connect.row_factory = sqlite3.Row
        cursor = connect.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?',[username])
        user = cursor.fetchone()

            #source for hashing: https://flask-bcrypt.readthedocs.io/en/1.0.1/index.html
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

@app.route('/adminForm', methods=['GET', 'POST'])
@adminLock
def adminForm():

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confpassword = request.form['confpassword']

        #insert users to the database
        with sqlite3.connect("database.db") as admins:
            cursor = admins.cursor()

            hash_password = bcrypt.generate_password_hash(password).decode('utf-8')
            bcrypt.generate_password_hash(hash_password)
            

            if password != confpassword:
                error="Your password and confirmed password need to be the same"
                return render_template('register.html', error=error) 

            cursor.execute("INSERT INTO admins \
                        (adminUsername, adminEmail, adminPassword, adminConfPassword) VALUES (?,?,?,?)",
                        (username, email, hash_password, hash_password))
            admins.commit()

        return redirect("/loginAdmin") 
    else: 
        return render_template('adminForm.html') 


@app.route('/loginAdmin', methods=['GET', 'POST'])
def loginAdmin():
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            connect = sqlite3.connect('database.db')
            connect.row_factory = sqlite3.Row
            cursor2 = connect.cursor()

            cursor2.execute('SELECT * FROM admins WHERE adminUsername = ?',[username])
            admin = cursor2.fetchone()

            if admin and bcrypt.check_password_hash(admin['adminPassword'], password):
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

@app.route('/speedtest')
@requiredLogin
def speedtest():
    speed_test = bandwidth_tests(socketio) 
    speed_test.start_speedtests()
    return render_template('speedtest.html')

@app.route('/networks')
@requiredLogin
def networks():
    return render_template('networks.html')

@app.route('/network')
@requiredLogin
def devices():
    return render_template('devices.html')

@socketio.on('disconnect')
def handle_disconnect():
    ssid_selector.stop_SSID_selection()



#settings and changing user info 
@app.route('/settingsHome')

def settingsHome():
    return render_template('settingsHome.html')

@app.route('/changePassword', methods=['GET', 'POST'])
def changePassword():
    min_length = 8
    uppercase_regex = re.compile(r'[A-Z]')
    lowercase_regex = re.compile(r'[a-z]')
    digit_regex = re.compile(r'\d')
    special_char_regex = re.compile(r'[!@#$%^&*()_+{}[\]:;<>,.?~\\/-]')
    if request.method == 'POST':
        username = request.form['username']
        newPassword =request.form['newPassword']
        confpassword = request.form['confpassword']

        connect = sqlite3.connect('database.db')
        connect.row_factory = sqlite3.Row
        cursor = connect.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', [username])
        user = cursor.fetchone()
       

            
        with sqlite3.connect("database.db") as users:
            hash_password = bcrypt.generate_password_hash(newPassword).decode('utf-8')
            bcrypt.generate_password_hash(hash_password)

            cursor2 = users.cursor()
                
            if user == None:
                errorCode = "username does not exist"
                return render_template('changePassword.html',error=errorCode)
                    
                
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
            
            cursor2.execute("UPDATE users  SET password =  (?), confpassword = (?) WHERE username = ?",
                                    (hash_password,hash_password,username))
            users.commit()

    return render_template('changePassword.html')

@app.route('/changeEmail',methods=['GET', 'POST'])

def changeEmail():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        newEmail =request.form['newEmail']

        connect = sqlite3.connect('database.db')
        connect.row_factory = sqlite3.Row
        cursor = connect.cursor()

        cursor.execute('SELECT username FROM users WHERE username = ?',[username])
        userCheck = cursor.fetchone()


        if not userCheck:
                return render_template('changeEmail.html', error = "Invalid username, please try again")

        with sqlite3.connect("database.db") as users:
            cursor = users.cursor()
            cursor.execute("UPDATE users  SET email =  (?) WHERE username = (?) AND email = (?)",
                        (newEmail,username,email))
            users.commit()

        return render_template('changeEmail.html',error="you have successfully changed you email")
    else:
        return render_template('changeEmail.html')

        
@app.route('/alerts')
@requiredLogin
def alerts():
    return render_template('alerts.html')

    
if __name__=='__main__':
    socketio.run(app)
    

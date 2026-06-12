from flask import Flask, render_template, request,flash, session, redirect
import sqlite3
#super cool functions to generate and check password password hashes
from werkzeug.security import generate_password_hash, check_password_hash

#create app
app = Flask(__name__)
#secret key needed gor sessions and flash messages
app.config['SECRET_KEY'] = "MyReallySecretKey"

#the path and filename for the database
DATABASE = "SimpleUserLogin/database.db"

#cool function to automatcally connect and query
def query_db(sql,args=(),one=False):
    '''connect and query- will return one item if one=true and can accept arguments as tuple'''
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    cursor.execute(sql, args)
    results = cursor.fetchall()
    db.commit()
    db.close()
    return (results[0] if results else None) if one else results


#routes go here
@app.route('/')
def index():
    return render_template('index.html')

#Now the cool dynamic route- each image that you click is an anchor tag that 
#passes an id to this route- we then query for THIS item and send just that 
#data to a template.
@app.route('/login', methods=["GET","POST"])
def login():
    #if the user posts a username and password
    if request.method == "POST":
        #get the username and password
        username = request.form['username']
        password = request.form['password']
        #try to find this user in the database- note- just keepin' it simple so usernames must be unique
        sql = "SELECT * FROM user WHERE username = ?"
        user = query_db(sql=sql,args=(username,),one=True)
        if user:
            #we got a user!!
            #check password matches-
            if check_password_hash(user[2],password):
                #we are logged in successfully
                #Store the username in the session
                session['user'] = user
                flash("Logged in successfully")
            else:
                flash("Password incorrect")
        else:
            flash("Username does not exist")
    #render this template regardles of get/post
    return render_template('login.html')


@app.route('/signup', methods=["GET","POST"])
def signup():
    #if the user posts from the signup page
    if request.method == "POST":
        #add the new username and hashed password to the database
        username = request.form['username']
        password = request.form['password']
        #hash it with the cool secutiry function
        hashed_password = generate_password_hash(password)
        #write it as a new user to the database
        sql = "INSERT INTO user (username,password) VALUES (?,?)"
        query_db(sql,(username,hashed_password))
        #message flashes exist in the base.html template and give user feedback
        flash("Sign Up Successful")
    return render_template('signup.html')


@app.route('/logout')
def logout():
    #just clear the username from the session and redirect back to the home page
    session['user'] = None
    return redirect('/')



#this bit of code runs the app that we just made with debug on
if __name__ == "__main__":
    app.run(debug=True)
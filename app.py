import sqlite3

from flask import Flask, g, render_template, request, flash, session, redirect
#super cool functions to generate and check password password hashes
from werkzeug.security import generate_password_hash, check_password_hash

#initialize app
app = Flask(__name__)

#secret key needed gor sessions and flash messages
app.config['SECRET_KEY'] = "MyReallySecretKey"


DATABASE = 'canteen_database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()



@app.route('/')
def home():
    db = get_db()
    db.row_factory = sqlite3.Row 
    cursor = db.cursor()

    sql = "SELECT item_name, item_ID, item_type, price, is_available, item_photo " \
    "FROM Menu WHERE is_available = 1;"

    cursor.execute(sql)
    results = cursor.fetchall()

    return render_template("home_user.html", menu_items=results)


def query_db(query, args=(), one=False):
    cursor = get_db().execute(query, args)
    rv = cursor.fetchall()
    cursor.close()
    return (rv[0] if rv else None) if one else rv



@app.route('/<int:item_ID>')
def item(item_ID): 
    db = get_db() 
    db.row_factory = sqlite3.Row 
    cursor = db.cursor()

    sql = "SELECT item_name, item_ID, item_type, price, is_available, item_photo " \
          "FROM Menu WHERE is_available = 1 AND item_ID = ?;"

    cursor.execute(sql, (item_ID,)) 

    result = cursor.fetchone() 
    
    return render_template("item_display.html", item=result)


@app.route('/home/<string:item_type>')
def catergory(item_type):
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    sql = "SELECT item_name, item_ID, item_type, price, is_available, item_photo " \
              "FROM Menu WHERE (is_available = 1 AND item_type = ?);"

    cursor.execute(sql, (item_type,))

    result = cursor.fetchall()

    return render_template("home_user.html", menu_items=result, category_name=item_type)

#login function
@app.route('/login', methods=["GET", "POST"])
def user_login():
    #if a user submits their form
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        
        #fetch user from database
        sql = "SELECT * FROM User WHERE username = ?"
        user = query_db(sql, args=(username,), one=True)
        
        #Check if user exists and if password hash matches
        if user and check_password_hash(user['password'], password):
            #store identifier in session
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            flash("Logged in successfully!")
            return redirect('/')
        else:
            flash("Invalid username or password.")

    #goes back to login page
    return render_template('login.html')

"""
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

"""


@app.route('/trolley')
def trolley():
    return render_template('trolley.html')

@app.route('/logout')
def logout():
    #just clear the username from the session and redirect back to the home page
    session['user'] = None
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)

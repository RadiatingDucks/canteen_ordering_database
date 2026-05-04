from flask import Flask, g, render_template

import sqlite3

DATABASE = 'canteen_database.db'

#initialize app
app = Flask(__name__)

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
    db =get_db()
    db.row_factory = sqlite3.Row 
    cursor = db.cursor()

    sql = "SELECT item_name, item_type, price, is_available, item_photo " \
    "FROM Menu;"

    cursor.execute(sql)
    results = cursor.fetchall()

    return render_template("home_user.html", menu_items=results)

def query_db(query, args=(), one=False):
    cursor = get_db().execute(query, args)
    rv = cursor.fetchall()
    cursor.close()
    return (rv[0] if rv else None) if one else rv

if __name__ == "__main__":
    app.run(debug=True)
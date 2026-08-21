#for activating venv: .\venv\Scripts\activate
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

    return render_template("home_user.html", menu_items=results, total=get_trolley_total())


def query_db(query, args=(), one=False):
    db = get_db()
    db.row_factory = sqlite3.Row
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
    
    return render_template("item_display.html", item=result, total=get_trolley_total())


@app.route('/home/<string:item_type>')
def catergory(item_type):
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    sql = "SELECT item_name, item_ID, item_type, price, is_available, item_photo " \
              "FROM Menu WHERE (is_available = 1 AND item_type = ?);"

    cursor.execute(sql, (item_type,))

    result = cursor.fetchall()

    return render_template("home_user.html", menu_items=result, category_name=item_type, total=get_trolley_total())

#login function
@app.route('/login', methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        # Form inputs
        user_input = request.form['username']
        password = request.form['password']
        
        # getting user by ID
        sql = "SELECT * FROM User WHERE ID = ?"
        user = query_db(sql, args=(user_input,), one=True)
        
        #Check if user exists and checks password
        if user and check_password_hash(user['password_hash'], password):
            #Store IDs/Details in session using column names
            session['user_id'] = user['ID']
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            
            flash("Logged in successfully!")
            return redirect('/')
        else:
            flash("Invalid ID or password.")

    return render_template('login.html')


@app.route('/signup', methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        # Get information from the form
        user_id = request.form['ID']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check that passwords match
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template('signup.html')

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Add user to database
        db = get_db()

        try:
            db.execute(
                """
                INSERT INTO User (ID, first_name, last_name, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, first_name, last_name, hashed_password)
            )

            db.commit()

        except sqlite3.IntegrityError:
            flash("That ID is already registered.")
            return render_template('signup.html')

        flash("Sign up successful! You can now log in.")
        return redirect('/login')

    return render_template('signup.html')

# route for the search bar
@app.route('/search')
def search():
    #asks for the query through the query-string arguements
    search_query = request.args.get('query', '')

    #SQL code that asks for a item_name like search_query
    sql = """
        SELECT item_name, item_ID, item_type, price, is_available, item_photo
        FROM Menu
        WHERE is_available = 1
        AND item_name LIKE ?
    """

    results = query_db(sql, ('%' + search_query + '%',))

    #returns to same template as home_user.html since layout is the same
    return render_template(
        'home_user.html',
        menu_items=results,
        #displays search query
        search_query=search_query,
        total=get_trolley_total()
    )

@app.route('/add_to_trolley', methods=['POST'])
def add_to_trolley():
    # Make sure the user is logged in
    if 'user_id' not in session:
        return {
            'success': False,
            'message': 'You must be logged in.'
        }, 401

    # Get information sent by JavaScript
    data = request.get_json()

    item_ID = data.get('item_ID')
    quantity = int(data.get('quantity', 1))

    # Make sure quantity is valid
    if quantity < 1:
        return {
            'success': False,
            'message': 'Invalid quantity.'
        }, 400

    user_ID = session['user_id']

    db = get_db()
    db.row_factory = sqlite3.Row

    # Check that the item actually exists and is available
    item = db.execute(
        """
        SELECT item_ID
        FROM Menu
        WHERE item_ID = ?
        AND is_available = 1
        """,
        (item_ID,)
    ).fetchone()

    if item is None:
        return {
            'success': False,
            'message': 'Item is not available.'
        }, 400

    # Check whether the item is already in the trolley
    existing_item = db.execute(
        """
        SELECT quantity
        FROM Trolley
        WHERE user_ID = ?
        AND item_ID = ?
        """,
        (user_ID, item_ID)
    ).fetchone()

    if existing_item:

        # Item already exists → increase quantity
        db.execute(
            """
            UPDATE Trolley
            SET quantity = quantity + ?
            WHERE user_ID = ?
            AND item_ID = ?
            """,
            (quantity, user_ID, item_ID)
        )

    else:

        # Item isn't in trolley → create new row
        db.execute(
            """
            INSERT INTO Trolley
            (user_ID, item_ID, quantity)
            VALUES (?, ?, ?)
            """,
            (user_ID, item_ID, quantity)
        )

    db.commit()

    return {
        'success': True,
        'message': 'Item added to trolley!'
    }

@app.route('/remove_from_trolley', methods=['POST'])
def remove_from_trolley():

    if 'user_id' not in session:
        return {
            'success': False,
            'message': 'You must be logged in.'
        }, 401

    data = request.get_json()

    item_ID = data.get('item_ID')
    user_ID = session['user_id']

    db = get_db()

    db.execute(
        """
        DELETE FROM Trolley
        WHERE user_ID = ?
        AND item_ID = ?
        """,
        (user_ID, item_ID)
    )

    db.commit()

    return {
        'success': True,
        'message': 'Item removed from trolley.'
    }


@app.route('/trolley')
def trolley():

    # Make sure user is logged in
    if 'user_id' not in session:
        return redirect('/login')

    user_ID = session['user_id']

    db = get_db()
    db.row_factory = sqlite3.Row

    trolley_items = db.execute(
        """
        SELECT
            Trolley.trolley_ID,
            Trolley.item_ID,
            Trolley.quantity,
            Menu.item_name,
            Menu.price,
            Menu.item_photo
        FROM Trolley
        JOIN Menu
            ON Trolley.item_ID = Menu.item_ID
        WHERE Trolley.user_ID = ?
        """,
        (user_ID,)
    ).fetchall()

    # Calculate total price
    total = sum(
        item['price'] * item['quantity']
        for item in trolley_items
    )

    return render_template(
        'trolley.html',
        trolley_items=trolley_items,
        total=total
    )

def get_trolley_total():
    if 'user_id' not in session:
        return 0.0

    user_ID = session['user_id']
    db = get_db()
    db.row_factory = sqlite3.Row

    trolley_items = db.execute(
        """
        SELECT Menu.price, Trolley.quantity
        FROM Trolley
        JOIN Menu ON Trolley.item_ID = Menu.item_ID
        WHERE Trolley.user_ID = ?
        """,
        (user_ID,)
    ).fetchall()

    return sum(item['price'] * item['quantity'] for item in trolley_items)

@app.route('/logout')
def logout():
    #clearing the session
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)

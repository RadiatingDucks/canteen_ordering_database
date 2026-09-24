"""app.py made by Amy Lian 2026"""
# for activating venv: .\venv\Scripts\activate
import sqlite3
from datetime import datetime

# import flask tools for web requests, templates, sessions, and redirects
from flask import Flask, g, render_template, request, flash, session, redirect
# functions to generate and check password hashes
from werkzeug.security import generate_password_hash, check_password_hash

# initialize app
app = Flask(__name__)

# secret key needed for sessions and flash messages
app.config['SECRET_KEY'] = "MyReallySecretKey"

# database file path
DATABASE = 'canteen_database.db'


def get_db():
    """Returns the current database connection or creates a new one."""
    # check if a database connection already exists in application context
    db = getattr(g, '_database', None)

    # if there is no database connection, create a new one as db
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    # return database connection object
    return db


# when flask request is finished
@app.teardown_appcontext
def close_connection(_exception):
    """Function that closes database connections"""
    # fetch existing connection from context
    db = getattr(g, '_database', None)

    # if connection exists, close it
    if db is not None:
        db.close()


# home page route
@app.route('/')
def home():
    """Function for displaying items in User Home page"""
    # get active database connection
    db = get_db()
    # configure database rows to be accessible like dictionaries
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # sql which gets info from items to display
    sql = ("SELECT item_name, item_ID, item_type, price, is_available, item_photo "
           "FROM Menu WHERE is_available = 1;")

    # execute the SQL command
    cursor.execute(sql)

    # get all the results from query
    results = cursor.fetchall()

    # close cursor after execution
    cursor.close()

    # sends the user to the home_user.html render template with menu items and trolley total
    return render_template(
        "home_user.html",
        menu_items=results,
        total=get_trolley_total()
    )


def query_db(query, args=(), one=False):
    """Function used for database queries to avoid repeated code"""
    # get active database connection
    db = get_db()
    # enable dictionary access for row results
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # execute the SQL query with arguments
    cursor.execute(query, args)

    # get all the results
    rv = cursor.fetchall()

    # close cursor
    cursor.close()

    # return single row if one parameter is True, otherwise return full list
    return (rv[0] if rv else None) if one else rv


# dynamic route for displaying individual item details
@app.route('/<int:item_id>')
def item(item_id):
    """Function which outputs one item's details"""
    # get database connection
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # SQL query to select details for specific item ID
    sql = """SELECT item_name,
            item_ID,
            item_type,
            price,
            is_available, 
            item_photo, 
            item_description
          FROM Menu WHERE is_available = 1 AND item_ID = ?;"""

    # execute the SQL code where item_id = what user selected
    cursor.execute(sql, (item_id,))

    # fetch the single resulting row
    result = cursor.fetchone()

    # close cursor
    cursor.close()

    # direct user to item_display page with item data and current trolley total
    return render_template("item_display.html", item=result, total=get_trolley_total())


# item category route
@app.route('/home/<string:item_type>')
def catergory(item_type):
    """Function that finds different types of foods"""
    # get database connection
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # SQL query to select menu items by category type
    sql = ("SELECT item_name, item_ID, item_type, price, is_available, item_photo "
           "FROM Menu WHERE (is_available = 1 AND item_type = ?);")

    # execute the code where item_type is the one the user selected
    cursor.execute(sql, (item_type,))

    # fetch the results for this category
    result = cursor.fetchall()

    # close cursor
    cursor.close()

    # direct the user to home_user.html with filtered items
    return render_template(
        "home_user.html",
        menu_items=result,
        category_name=item_type,
        total=get_trolley_total()
    )


# login function
@app.route('/login', methods=["GET", "POST"])
def user_login():
    """Function that takes inputs to create user session"""
    # check if form was submitted via POST
    if request.method == "POST":

        # Form inputs from request
        user_input = request.form['username']
        password = request.form['password']

        # getting user by ID from database
        sql = "SELECT ID, password_hash, first_name, last_name FROM User WHERE ID = ?"
        user = query_db(sql, args=(user_input,), one=True)

        # Check if user exists and checks password hash against input
        if user and check_password_hash(user['password_hash'], password):

            # Store IDs/Details in session using column names
            session['user_id'] = user['ID']
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']

            # flash success message and redirect home
            flash("Logged in successfully!")
            return redirect('/')

        # flash error message if credentials do not match
        flash("Invalid ID or password.")

    # render login template for GET request or failed login
    return render_template('login.html')


# sign up function
@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Function which takes user information for inputs and pushes it to database"""
    # check if form was submitted
    if request.method == "POST":

        # Get information from the form fields
        user_id = request.form['ID']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check that passwords match before proceeding
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template('signup.html')

        # Hash the password for secure storage
        hashed_password = generate_password_hash(password)

        # Add user to database connection
        db = get_db()
        cursor = db.cursor()

        try:
            # SQL to add the new user into database table
            cursor.execute(
                """
                INSERT INTO User (ID, first_name, last_name, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, first_name, last_name, hashed_password)
            )

            # commit changes to database
            db.commit()

        except sqlite3.IntegrityError:
            # handle duplicate ID entry error
            flash("That ID is already registered.")
            cursor.close()
            return render_template('signup.html')

        # close cursor
        cursor.close()

        # flash success message and redirect to login page
        flash("Sign up successful! You can now log in.")
        return redirect('/login')

    # render signup template for GET request
    return render_template('signup.html')


# search route
@app.route('/search')
def search():
    """Function for search bar which compares input with item_name in database"""
    # asks for the query through the query-string arguments
    search_query = request.args.get('query', '')

    # SQL code that asks for an item_name like search_query using wildcards
    sql = """
        SELECT item_name, item_ID, item_type, price, is_available, item_photo
        FROM Menu
        WHERE is_available = 1
        AND item_name LIKE ?
    """

    # execute query function with search parameters
    results = query_db(sql, ('%' + search_query + '%',))

    # returns to same template as home_user.html since layout is the same
    return render_template(
        'home_user.html',
        menu_items=results,
        search_query=search_query,
        total=get_trolley_total()
    )


# adds item to trolley
@app.route('/add_to_trolley', methods=['POST'])
def add_to_trolley():
    """Function that checks request validity then inserts added item to trolley"""
    # checks if user is signed in before allowing trolley addition
    if 'user_id' not in session:
        return {'success': False, 'message': 'You must be logged in.'}, 401

    # variables extracted from JSON request payload
    data = request.get_json() or {}
    item_id = data.get('item_ID')

    # Strict integer conversion(except errors)
    try:
        quantity = int(data.get('quantity', 1))
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid quantity entered.'}, 400

    # Reject negative quantities or single orders more than 10
    if quantity < 1 or quantity > 10:
        return {'success': False, 'message': 'Quantity must be between 1 and 10.'}, 400

    # get logged-in user ID from session
    user_id = session['user_id']

    # get database connection
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # check if the item exists and is available in menu
    cursor.execute(
        "SELECT item_ID FROM Menu WHERE item_ID = ? AND is_available = 1",
        (item_id,)
    )
    trolley_item = cursor.fetchone()

    # return error if item is missing or unavailable
    if trolley_item is None:
        cursor.close()
        return {'success': False, 'message': 'Item is not available.'}, 400

    # check if the item is already in the trolley for this user
    cursor.execute(
        "SELECT quantity FROM Trolley WHERE user_ID = ? AND item_ID = ?",
        (user_id, item_id)
    )
    existing_item = cursor.fetchone()

    # Check total in cart (max 10 total per item)
    current_qty = existing_item['quantity'] if existing_item else 0

    # enforce maximum limit of 10 items per menu item
    if current_qty + quantity > 10:
        cursor.close()
        msg = f'You already have {current_qty} in your cart. Maximum limit is 10 per item.'
        return {
            'success': False,
            'message': msg
        }, 400

    if existing_item:

        # update the quantity if item is already in trolley
        cursor.execute(
            "UPDATE Trolley SET quantity = quantity + ? WHERE user_ID = ? AND item_ID = ?",
            (quantity, user_id, item_id)
        )

    else:

        # add a new item to the trolley
        cursor.execute(
            "INSERT INTO Trolley (user_ID, item_ID, quantity) VALUES (?, ?, ?)",
            (user_id, item_id, quantity)
        )

    # commit trolley update to database
    db.commit()

    # close cursor
    cursor.close()

    # calculate new total price after addition
    new_total = get_trolley_total()

    # return JSON response to AJAX call
    return {
        'success': True,
        'message': 'Item added to trolley!',
        'new_total': new_total
    }


# remove items from trolley
@app.route('/remove_from_trolley', methods=['POST'])
def remove_from_trolley():
    """Function that deletes items from Trolley and calculates new total"""
    # checks if user is signed in
    if 'user_id' not in session:
        return {'success': False, 'message': 'You must be logged in.'}, 401

    # get item ID from payload and user ID from session
    data = request.get_json()
    item_id = data.get('item_ID')
    user_id = session['user_id']

    # get database cursor
    db = get_db()
    cursor = db.cursor()

    # Delete the item matching user ID and item ID
    cursor.execute(
        """
        DELETE FROM Trolley
        WHERE user_ID = ? AND item_ID = ?
        """,
        (user_id, item_id)
    )

    # save changes to database
    db.commit()

    # Calculate remaining total by joining trolley with menu prices
    db.row_factory = sqlite3.Row

    cursor.execute(
        """
        SELECT Menu.price, Trolley.quantity
        FROM Trolley
        JOIN Menu ON Trolley.item_ID = Menu.item_ID
        WHERE Trolley.user_ID = ?
        """,
        (user_id,)
    )

    # fetch updated trolley items
    trolley_items = cursor.fetchall()

    # sum prices for all remaining items in trolley
    new_total = sum(item_data['price'] * item_data['quantity'] for item_data in trolley_items)

    # close cursor
    cursor.close()

    # return JSON response with updated stats
    return {
        'success': True,
        'message': 'Item removed from trolley.',
        'new_total': new_total,
        'item_count': len(trolley_items)
    }


# trolley display route
@app.route('/trolley')
def trolley():
    """Function which outputs items user has ordered"""
    # Make sure user is logged in
    if 'user_id' not in session:
        return redirect('/login')

    # store active user ID
    user_id = session['user_id']

    # get database cursor
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # get all items currently in the user's trolley with details from menu
    cursor.execute(
        """
        SELECT Trolley.trolley_ID, Trolley.item_ID, Trolley.quantity,
               Menu.item_name, Menu.price, Menu.item_photo
        FROM Trolley
        JOIN Menu ON Trolley.item_ID = Menu.item_ID
        WHERE Trolley.user_ID = ?
        """,
        (user_id,)
    )

    # store query results
    trolley_items = cursor.fetchall()

    # close cursor
    cursor.close()

    # Calculate total price of trolley items
    total = sum(
        item_data['price'] * item_data['quantity']
        for item_data in trolley_items
    )

    # render trolley view template
    return render_template(
        'trolley.html',
        trolley_items=trolley_items,
        total=total
    )


def get_trolley_total():
    """function for getting total price"""
    # checks if user is signed in
    if 'user_id' not in session:
        return 0.0

    # fetch user ID
    user_id = session['user_id']

    # get database connection
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # gets the price and quantity for active user's trolley items
    cursor.execute(
        """
        SELECT Menu.price, Trolley.quantity
        FROM Trolley
        JOIN Menu ON Trolley.item_ID = Menu.item_ID
        WHERE Trolley.user_ID = ?
        """,
        (user_id,)
    )

    # store results
    trolley_items = cursor.fetchall()

    # close cursor
    cursor.close()

    # sum of all the items' price times quantity which gives total
    return sum(item_data['price'] * item_data['quantity'] for item_data in trolley_items)


# checkout processing route
@app.route('/checkout', methods=['POST'])
def checkout():
    """Function which finds total price and pushes order to 'Orders' database"""
    # checks if user is signed in
    if 'user_id' not in session:
        return redirect('/login')

    # store session user ID
    user_id = session['user_id']

    # get database handle
    db = get_db()
    db.row_factory = sqlite3.Row

    # Fetch items currently in the user's trolley
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT Trolley.item_ID, Trolley.quantity, Menu.price
        FROM Trolley
        JOIN Menu ON Trolley.item_ID = Menu.item_ID
        WHERE Trolley.user_ID = ?
        """,
        (user_id,)
    )

    # store items array
    trolley_items = cursor.fetchall()

    # close cursor
    cursor.close()

    # if there's no trolley items, prevent checkout
    if not trolley_items:
        flash("Your trolley is empty.")
        return redirect('/trolley')

    # Calculate total price for order record
    total_price = sum(
        item_data['price'] * item_data['quantity']
        for item_data in trolley_items
    )

    # record current date and time string
    order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = 0  # 0 = Pending/Unfulfilled

    try:
        # create a new cursor for inserting the order
        cursor = db.cursor()

        # 1. Insert into 'order' table
        cursor.execute(
            """
            INSERT INTO "Order" (student_ID, order_date, total_price, status)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, order_date, total_price, status)
        )

        # get auto-generated order ID from last row
        order_id = cursor.lastrowid

        # Insert items into Order_Detail table using order ID
        for item_data in trolley_items:
            cursor.execute(
                """
                INSERT INTO Order_Detail (order_ID, item_ID, quantity)
                VALUES (?, ?, ?)
                """,
                (order_id, item_data['item_ID'], item_data['quantity'])
            )

        # Clear user's trolley after successful order placement
        cursor.execute(
            "DELETE FROM Trolley WHERE user_ID = ?",
            (user_id,)
        )

        # commit transaction to database
        db.commit()

        # close cursor
        cursor.close()

        # notify user and redirect
        flash("Order placed successfully!")
        return redirect('/trolley')

    except sqlite3.Error:

        # close cursor if an error happens
        cursor.close()

        # undo transaction if error occurs
        db.rollback()
        flash("There was an issue processing your order.")
        return redirect('/trolley')


# order history route
@app.route('/order_history')
def order_history():
    """Function which returns the user's past orders"""

    # checks if user is signed in
    if 'user_id' not in session:
        return redirect('/login')

    # store active user ID
    user_id = session['user_id']

    # get database connection
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Fetch all orders for the logged-in student, newest first
    cursor.execute(
        """
        SELECT order_ID, order_date, total_price, status
        FROM "Order"
        WHERE student_ID = ?
        ORDER BY order_date DESC
        """,
        (user_id,)
    )

    # store order history records
    orders = cursor.fetchall()

    # close cursor
    cursor.close()

    # render order history view
    return render_template(
        'order_history.html',
        orders=orders,
        total=get_trolley_total()
    )


# individual order details route
@app.route('/order/<int:order_id>')
def order_detail(order_id):
    """Function which outputs user's order details"""

    # checks if user is signed in
    if 'user_id' not in session:
        return redirect('/login')

    # store active user ID
    user_id = session['user_id']

    # get database connection
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Fetch order details only if it belongs to the logged-in user
    cursor.execute(
        """
        SELECT order_ID, order_date, total_price, status
        FROM "Order"
        WHERE order_ID = ? AND student_ID = ?
        """,
        (order_id, user_id)
    )

    # store single order header
    order = cursor.fetchone()

    # handle non-existent order or access attempt to another user's order
    if not order:
        cursor.close()
        flash("Order not found or access denied.")
        return redirect('/order_history')

    # Fetch line items for this specific order
    cursor.execute(
        """
        SELECT Menu.item_name, Menu.price, Menu.item_photo, Order_Detail.quantity
        FROM Order_Detail
        JOIN Menu ON Order_Detail.item_ID = Menu.item_ID
        WHERE Order_Detail.order_ID = ?
        """,
        (order_id,)
    )

    # store line items list
    items = cursor.fetchall()

    # close cursor
    cursor.close()

    # render order detail view
    return render_template(
        'order_detail.html',
        order=order,
        items=items,
        total=get_trolley_total()
    )


# error handlers
@app.errorhandler(404)
def page_not_found(_e):
    """Function which directs user to 404 error page"""
    # return custom 404 template with HTTP status code 404
    return render_template(
        '404.html',
        total=get_trolley_total()
    ), 404


@app.errorhandler(500)
def internal_server_error(_e):
    """Function which directs user to 500 error page"""
    # return custom 500 template with HTTP status code 500
    return render_template(
        '500.html',
        total=get_trolley_total()
    ), 500


# log out route
@app.route('/logout')
def logout():
    """Function which logs user out of their session"""

    # clearing the session data completely
    session.clear()

    # Redirect to home page
    return redirect('/')


# entry point to run development server
if __name__ == "__main__":
    app.run(debug=True)

#for activating venv: .\venv\Scripts\activate
import sqlite3

from flask import Flask, g, render_template, request, flash, session, redirect

#super cool functions to generate and check password password hashes
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime

#initialize app
app = Flask(__name__)

#secret key needed gor sessions and flash messages
app.config['SECRET_KEY'] = "MyReallySecretKey"

#database
DATABASE = 'canteen_database.db'


def get_db():
    db = getattr(g, '_database', None)

    #if there is no database connection, create a new one as db
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)

    #return database
    return db


#when flask request is finished
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)

    #if conection exists, close it
    if db is not None:
        db.close()


#home page
@app.route('/')
#home page function
def home():
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    #sql which gets info from items to display
    sql = "SELECT item_name, item_ID, item_type, price, is_available, item_photo " \
          "FROM Menu WHERE is_available = 1;"

    #execute the SQL
    cursor.execute(sql)

    #get all the results
    results = cursor.fetchall()

    #close cursor
    cursor.close()

    #sends the user to the home_user.html, where results = menu_items(html) and total = get_trolley_total()
    return render_template("home_user.html", menu_items=results, total=get_trolley_total())


#database-query function
def query_db(query, args=(), one=False):
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    #execute the SQL query
    cursor.execute(query, args)

    #get all the results
    rv = cursor.fetchall()

    #close cursor
    cursor.close()

    return (rv[0] if rv else None) if one else rv


#item display 
@app.route('/<int:item_ID>')
def item(item_ID): 
    db = get_db() 
    db.row_factory = sqlite3.Row 
    cursor = db.cursor()

    #SQL
    sql = "SELECT item_name, item_ID, item_type, price, is_available, item_photo, item_description " \
          "FROM Menu WHERE is_available = 1 AND item_ID = ?;"

    #execute the SQL code where item_ID = what user selected
    cursor.execute(sql, (item_ID,))

    #fetch the result
    result = cursor.fetchone()

    #close cursor
    cursor.close()

    #direct user to item_display page where the result = item(html) and total = get_trolley_total
    return render_template("item_display.html", item=result, total=get_trolley_total())


#item catergory
@app.route('/home/<string:item_type>')
def catergory(item_type):
    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    #SQL
    sql = "SELECT item_name, item_ID, item_type, price, is_available, item_photo " \
          "FROM Menu WHERE (is_available = 1 AND item_type = ?);"

    #execute the code where item_type is the one the user selected
    cursor.execute(sql, (item_type,))

    #fetch the results
    result = cursor.fetchall()

    #close cursor
    cursor.close()

    #direct the user to the render template home_user.html where catergory name = the item type the user entered
    return render_template(
        "home_user.html",
        menu_items=result,
        category_name=item_type,
        total=get_trolley_total()
    )


#login function
@app.route('/login', methods=["GET", "POST"])
def user_login():
    if request.method == "POST":

        # Form inputs
        user_input = request.form['username']
        password = request.form['password']

        # getting user by ID
        sql = "SELECT ID, password_hash, first_name, last_name FROM User WHERE ID = ?"
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
        cursor = db.cursor()

        try:
            #SQL to add the new user
            cursor.execute(
                """
                INSERT INTO User (ID, first_name, last_name, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, first_name, last_name, hashed_password)
            )

            db.commit()

        except sqlite3.IntegrityError:
            flash("That ID is already registered.")
            cursor.close()
            return render_template('signup.html')

        #close cursor
        cursor.close()

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
        search_query=search_query,
        total=get_trolley_total()
    )


#adds item to trolley
@app.route('/add_to_trolley', methods=['POST'])
def add_to_trolley():

    #checks if user is signed in
    if 'user_id' not in session:
        return {'success': False, 'message': 'You must be logged in.'}, 401

    #variables
    data = request.get_json() or {}
    item_ID = data.get('item_ID')

    #Strict integer conversion(except errors)
    try:
        quantity = int(data.get('quantity', 1))
    except (ValueError, TypeError):
        return {'success': False, 'message': 'Invalid quantity entered.'}, 400

    #Reject negative quantities or single orders more than 10
    if quantity < 1 or quantity > 10:
        return {'success': False, 'message': 'Quantity must be between 1 and 10.'}, 400

    user_ID = session['user_id']

    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    #check if the item exists and is available
    cursor.execute(
        "SELECT item_ID FROM Menu WHERE item_ID = ? AND is_available = 1",
        (item_ID,)
    )
    item = cursor.fetchone()

    if item is None:
        cursor.close()
        return {'success': False, 'message': 'Item is not available.'}, 400

    #check if the item is already in the trolley
    cursor.execute(
        "SELECT quantity FROM Trolley WHERE user_ID = ? AND item_ID = ?",
        (user_ID, item_ID)
    )
    existing_item = cursor.fetchone()

    #Check total in cart (max 10 total per item)
    current_qty = existing_item['quantity'] if existing_item else 0

    if current_qty + quantity > 10:
        cursor.close()
        return {
            'success': False,
            'message': f'You already have {current_qty} in your cart. Maximum limit is 10 per item.'
        }, 400

    if existing_item:

        #update the quantity if item is already in trolley
        cursor.execute(
            "UPDATE Trolley SET quantity = quantity + ? WHERE user_ID = ? AND item_ID = ?",
            (quantity, user_ID, item_ID)
        )

    else:

        #add a new item to the trolley
        cursor.execute(
            "INSERT INTO Trolley (user_ID, item_ID, quantity) VALUES (?, ?, ?)",
            (user_ID, item_ID, quantity)
        )

    db.commit()

    #close cursor
    cursor.close()

    new_total = get_trolley_total()

    return {
        'success': True,
        'message': 'Item added to trolley!',
        'new_total': new_total
    }


#remove items from trolley
@app.route('/remove_from_trolley', methods=['POST'])
def remove_from_trolley():

    #checks if user is signed in
    if 'user_id' not in session:
        return {'success': False, 'message': 'You must be logged in.'}, 401

    data = request.get_json()
    item_ID = data.get('item_ID')
    user_ID = session['user_id']

    db = get_db()
    cursor = db.cursor()

    #Delete the item
    cursor.execute(
        """
        DELETE FROM Trolley
        WHERE user_ID = ? AND item_ID = ?
        """,
        (user_ID, item_ID)
    )

    db.commit()

    #Calculate remaining total
    db.row_factory = sqlite3.Row

    cursor.execute(
        """
        SELECT Menu.price, Trolley.quantity
        FROM Trolley
        JOIN Menu ON Trolley.item_ID = Menu.item_ID
        WHERE Trolley.user_ID = ?
        """,
        (user_ID,)
    )

    trolley_items = cursor.fetchall()

    new_total = sum(item['price'] * item['quantity'] for item in trolley_items)

    #close cursor
    cursor.close()

    return {
        'success': True,
        'message': 'Item removed from trolley.',
        'new_total': new_total,
        'item_count': len(trolley_items)
    }


#trolley display
@app.route('/trolley')
def trolley():

    #Make sure user is logged in
    if 'user_id' not in session:
        return redirect('/login')

    user_ID = session['user_id']

    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    #get all items currently in the user's trolley
    cursor.execute(
        """
        SELECT Trolley.trolley_ID, Trolley.item_ID, Trolley.quantity,
               Menu.item_name, Menu.price, Menu.item_photo
        FROM Trolley
        JOIN Menu ON Trolley.item_ID = Menu.item_ID
        WHERE Trolley.user_ID = ?
        """,
        (user_ID,)
    )

    trolley_items = cursor.fetchall()

    #close cursor
    cursor.close()

    #Calculate total price
    total = sum(
        item['price'] * item['quantity']
        for item in trolley_items
    )

    return render_template(
        'trolley.html',
        trolley_items=trolley_items,
        total=total
    )


#function for getting total price
def get_trolley_total():

    #checks if signed in
    if 'user_id' not in session:
        return 0.0

    user_ID = session['user_id']

    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    #gets the price and quantity
    cursor.execute(
        """
        SELECT Menu.price, Trolley.quantity
        FROM Trolley
        JOIN Menu ON Trolley.item_ID = Menu.item_ID
        WHERE Trolley.user_ID = ?
        """,
        (user_ID,)
    )

    trolley_items = cursor.fetchall()

    #close cursor
    cursor.close()

    #sum of all the items' price times quantity which gives total
    return sum(item['price'] * item['quantity'] for item in trolley_items)


@app.route('/checkout', methods=['POST'])
def checkout():

    #checks if user is signed in
    if 'user_id' not in session:
        return redirect('/login')

    user_ID = session['user_id']

    db = get_db()
    db.row_factory = sqlite3.Row

    #Fetch items currently in the user's trolley
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT Trolley.item_ID, Trolley.quantity, Menu.price
        FROM Trolley
        JOIN Menu ON Trolley.item_ID = Menu.item_ID
        WHERE Trolley.user_ID = ?
        """,
        (user_ID,)
    )

    trolley_items = cursor.fetchall()

    #close cursor
    cursor.close()

    #if there's no trolley items
    if not trolley_items:
        flash("Your trolley is empty.")
        return redirect('/trolley')

    #Calculate total price
    total_price = sum(
        item['price'] * item['quantity']
        for item in trolley_items
    )

    order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = 0  # 0 = Pending/Unfulfilled

    try:
        #create a new cursor for inserting the order
        cursor = db.cursor()

        # 1. Insert into 'order' table
        cursor.execute(
            """
            INSERT INTO "Order" (student_ID, order_date, total_price, status)
            VALUES (?, ?, ?, ?)
            """,
            (user_ID, order_date, total_price, status)
        )

        order_ID = cursor.lastrowid

        # 2. Insert items into Order_Detail table
        for item in trolley_items:
            cursor.execute(
                """
                INSERT INTO Order_Detail (order_ID, item_ID, quantity)
                VALUES (?, ?, ?)
                """,
                (order_ID, item['item_ID'], item['quantity'])
            )

        # 3. Clear user's trolley
        cursor.execute(
            "DELETE FROM Trolley WHERE user_ID = ?",
            (user_ID,)
        )

        db.commit()

        #close cursor
        cursor.close()

        flash("Order placed successfully!")
        return redirect('/trolley')

    except sqlite3.Error as e:

        #close cursor if an error happens
        cursor.close()

        db.rollback()
        flash("There was an issue processing your order.")
        return redirect('/trolley')


@app.route('/order_history')
def order_history():

    #checks if user is signed in
    if 'user_id' not in session:
        return redirect('/login')

    user_ID = session['user_id']

    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    #Fetch all orders for the logged-in student, newest first
    cursor.execute(
        """
        SELECT order_ID, order_date, total_price, status
        FROM "Order"
        WHERE student_ID = ?
        ORDER BY order_date DESC
        """,
        (user_ID,)
    )

    orders = cursor.fetchall()

    #close cursor
    cursor.close()

    return render_template(
        'order_history.html',
        orders=orders,
        total=get_trolley_total()
    )


@app.route('/order/<int:order_ID>')
def order_detail(order_ID):

    #checks if user is signed in
    if 'user_id' not in session:
        return redirect('/login')

    user_ID = session['user_id']

    db = get_db()
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    #Fetch order details only if it belongs to the logged-in user
    cursor.execute(
        """
        SELECT order_ID, order_date, total_price, status
        FROM "Order"
        WHERE order_ID = ? AND student_ID = ?
        """,
        (order_ID, user_ID)
    )

    order = cursor.fetchone()

    if not order:
        cursor.close()
        flash("Order not found or access denied.")
        return redirect('/order_history')

    #Fetch line items for this specific order
    cursor.execute(
        """
        SELECT Menu.item_name, Menu.price, Menu.item_photo, Order_Detail.quantity
        FROM Order_Detail
        JOIN Menu ON Order_Detail.item_ID = Menu.item_ID
        WHERE Order_Detail.order_ID = ?
        """,
        (order_ID,)
    )

    items = cursor.fetchall()

    #close cursor
    cursor.close()

    return render_template(
        'order_detail.html',
        order=order,
        items=items,
        total=get_trolley_total()
    )


#error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        '404.html',
        total=get_trolley_total()
    ), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template(
        '500.html',
        total=get_trolley_total()
    ), 500


#log out
@app.route('/logout')
def logout():

    #clearing the session
    session.clear()

    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)

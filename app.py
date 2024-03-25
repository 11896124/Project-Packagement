import os
from flask_session import Session
from sqlalchemy import and_
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, redirect, render_template, request, session
from helpers import apology, login_required, convert_arrivaltime_dhl, convert_time
from models import db, Order, User
import datetime
import requests
import json

# Configure application
app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
db.init_app(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def main_menu():
    """Show lists of all Orders"""

    # this is the users id
    user_id = session["user_id"]

    # info list for main page message:
    order_list = Order.query.filter_by(order_user_id=user_id).all()
    number_of_orders: int = len(order_list)

    # query for barcode and postcode through one list
    get_list_of_postcodes = Order.query.filter(and_(Order.order_user_id == user_id, Order.postal_code.isnot(None))).all()

    for order in get_list_of_postcodes:
        barcode = order.barcode
        postal_code = order.postal_code
        # Update DHL orders
        if order.postal_service == "DHL":
            website = f"https://api-gw.dhlparcel.nl/track-trace?key={barcode}%2B{postal_code}&role=receiver"
            raw_json = requests.get(website).text
            json_data = json.loads(raw_json)

            # Check order status
            phases = json.dumps(json_data[0]["view"]["phases"])
            phases_list = json.loads(phases)
            if phases_list[0]["phase"] == "DELIVERED":
                order_status = "delivered"
            elif phases_list[0]["phase"] == "IN_DELIVERY":
                order_status = "in transition"
            elif phases_list[0]["phase"] != "IN_DELIVERY" and phases_list[0]["phase"] != "DELIVERED":
                order_status = "not sent"
            else:
                order_status = "unknown"

            # update order status
            Order.query.filter_by(order_number=order.order_number).update({"status": order_status})
            db.session.commit()

        # Update PostNl order
        elif order.postal_service == "PostNL":
            website = f"https://jouw.postnl.nl/track-and-trace/api/trackAndTrace/{barcode}-NL-{postal_code}?language=nl"
            raw_json = requests.get(website).text
            json_data = json.loads(raw_json)
            # change order status
            order_status = json_data["colli"][barcode]["statusPhase"]['index']
            if order_status == 4:
                order_status = "delivered"
            elif order_status != 4:
                order_status = "in transition"

            # update order status
            Order.query.filter_by(order_number=order.order_number).update({"status": order_status})
            db.session.commit()

    # create delivered list
    delivered_list = Order.query.filter(and_(Order.order_user_id == user_id, Order.status == "delivered")).all()
    # create in transition list
    in_transition_list = Order.query.filter(and_(Order.order_user_id == user_id, Order.status == "in transition")).all()
    # create not sent list
    not_sent_list = Order.query.filter(and_(Order.order_user_id == user_id, Order.status == "not sent")).all()

    # Sort the lists based on the order number
    delivered_list = sorted(delivered_list, key=lambda x: x.order_number_for_user)
    in_transition_list = sorted(in_transition_list, key=lambda x: x.order_number_for_user)
    not_sent_list = sorted(not_sent_list, key=lambda x: x.order_number_for_user)

    return render_template("main.html", order=Order.query.first(),
                           user=User.query.filter_by(id=user_id).first(),
                           order_list=order_list,
                           number_of_orders=number_of_orders,
                           delivered_list=delivered_list,
                           in_transition_list=in_transition_list,
                           not_sent_list=not_sent_list,
                           get_list_of_postcodes=get_list_of_postcodes)


@app.route("/trackandtrace", methods=["GET", "POST"])
@login_required
def add_trackandtrace_order():
    """Adds track and trace order to list of Orders"""
    # to ensure template is rendered if request method is "GET"
    if request.method == "GET":
        return render_template("trackandtrace.html", user=User.query.first())

    # get barcode
    barcode = request.form.get("barcode")
    # Ensure barcode was submitted
    if not request.form.get("barcode"):
        return apology("must provide barcode", 403)
    # add barcode to standards
    barcode = barcode.upper()

    # get post code
    postal_code = request.form.get("postal_code")
    # Ensure post_code was submitted
    if not request.form.get("postal_code"):
        return apology("must provide postal code", 403)
    # add postal_code to standards
    postal_code = postal_code.upper()

    # get which postal company
    postal_company = request.form.get("postal_company")
    if not request.form.get("postal_company"):
        return apology("must provide postal company", 403)

    if postal_company == "PostNL":
        # scrape the PostNl website for appropriate data
        website = f"https://jouw.postnl.nl/track-and-trace/api/trackAndTrace/{barcode}-NL-{postal_code}?language=nl"
        raw_json = requests.get(website).text
        json_data = json.loads(raw_json)

        # add user_id to order
        order_user_id = session.get("user_id")

        # add postal_service
        postal_service = "PostNL"

        # add order status
        order_status = json_data["colli"][barcode]["statusPhase"]['index']
        if order_status == 4:
            order_status = "delivered"
        elif order_status != 4:
            order_status = "in transition"

        # add date of arrival
        date_arrival = "Unkown for now"

        # add date created
        date = datetime.datetime.now()
        # gives it a simple format
        date_created = date.strftime('%Y-%m-%d %H:%M:%S')

        # unique order number for user
        order_number_for_user = len(Order.query.filter_by(order_user_id=session["user_id"]).all()) + 1

        # order name
        order_name = request.form.get("order_name")

        # adds information to database
        new_order = Order(order_user_id=order_user_id,
                          barcode=barcode,
                          postal_code=postal_code,
                          postal_service=postal_service,
                          status=order_status,
                          date_arrival=date_arrival,
                          date_created=date_created,
                          order_number_for_user=order_number_for_user,
                          order_name=order_name)
        db.session.add(new_order)
        db.session.commit()

    elif postal_company == "DHL":
        # different site to scrape from
        website = f"https://api-gw.dhlparcel.nl/track-trace?key={barcode}%2B{postal_code}&role=receiver"
        raw_json = requests.get(website).text
        json_data = json.loads(raw_json)

        # add user_id to order
        order_user_id = session.get("user_id")

        # add postal_service
        postal_service = "DHL"

        # Check order status
        phases = json.dumps(json_data[0]["view"]["phases"])
        phases_list = json.loads(phases)
        if phases_list[0]["phase"] == "DELIVERED":
            order_status = "delivered"
        elif phases_list[0]["phase"] == "IN_DELIVERY":
            order_status = "in transition"
        elif phases_list[0]["phase"] != "IN_DELIVERY" and phases_list[0]["phase"] != "DELIVERED":
            order_status = "not sent"
        else:
            order_status = "unknown"

        # add date of arrival
        date_arrival = json_data[0]["events"][3]["plannedDeliveryTimeframe"]
        date_arrival = convert_arrivaltime_dhl(date_arrival)

        # add date created
        date = datetime.datetime.now()
        # gives it a simple format
        date_created = date.strftime('%Y-%m-%d %H:%M:%S')

        # unique order number for user
        order_number_for_user = len(Order.query.filter_by(order_user_id=session["user_id"]).all()) + 1

        # order name
        order_name = request.form.get("order_name")

        # adds information to database
        new_order = Order(order_user_id=order_user_id,
                          barcode=barcode,
                          postal_code=postal_code,
                          postal_service=postal_service,
                          status=order_status,
                          date_arrival=date_arrival,
                          date_created=date_created,
                          order_number_for_user=order_number_for_user,
                          order_name=order_name)
        db.session.add(new_order)
        db.session.commit()

        return redirect("/")


@app.route("/add_order", methods=["GET", "POST"])
@login_required
def add_order():
    """Adds personal order to database"""
    # to ensure template is rendered if request method is "GET"
    if request.method == "GET":
        return render_template("add_order.html", user=User.query.first())

    # add user_id to order
    order_user_id = session.get("user_id")
    if order_user_id is None:
        return apology("User not logged in", 403)

    # add postal sevice
    postal_service = request.form.get("postal_service")

    # user must enter his order status
    order_status = request.form.get("order_status")
    if not order_status:
        return apology("must provide order status", 403)

    # user must enter his orders date of arrival
    date_arrival = request.form.get("date_arrival")
    if not date_arrival:
        return apology("must provide date of arrival", 403)
    # generated by chatgpt
    try:
        # Attempt to convert the input date string
        date_arrival = convert_time(date_arrival)
    except Exception as e:
        # Redirect to apology page with an error message
        return apology(f"Invalid date format: {str(e)}", 403)

    # Use converted_date as needed
    date_arrival.rsplit()
    date_arrival = convert_time(date_arrival)

    # add date created
    date = datetime.datetime.now()
    # gives it a simple format
    date_created = date.strftime('%Y-%m-%d %H:%M:%S')
    date_created = convert_time(date_created)

    # unique order number for user
    order_number_for_user = len(Order.query.filter_by(order_user_id=session["user_id"]).all()) + 1

    # order name
    order_name = request.form.get("order_name")

    # add the order to the database
    new_order = Order(order_user_id=order_user_id,
                      postal_service=postal_service,
                      status=order_status,
                      date_arrival=date_arrival,
                      date_created=date_created,
                      order_number_for_user=order_number_for_user,
                      order_name=order_name)
    db.session.add(new_order)
    db.session.commit()

    return redirect("/")


@app.route("/update_order", methods=["GET", "POST"])
@login_required
def update_order():
    """Allows user to update order, only update available now is a delete update"""

    if request.method == "POST":
        # get order number that only user can see in their list
        order_number = request.form.get("order_number_for_user")
        Order.query.filter(and_(Order.order_user_id == session["user_id"], Order.order_number_for_user == order_number)).delete()
        db.session.commit()
        return redirect("/")
    else:
        return render_template("update_order.html", user=User.query.first())


@app.route("/about", methods=["GET", "POST"])
@login_required
def about():
    """Gives user information and instruction on how to use the database"""

    if request.method == "POST":
        return redirect("/")
    else:
        return render_template("about.html", user=User.query.first())


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User must reach route via POST, this ensures that
    if request.method == "GET":
        return render_template("login.html")

    # Ensure username was submitted
    if not request.form.get("username"):
        return apology("Must provide username", 403)

    # Ensure password was submitted
    elif not request.form.get("password"):
        return apology("Must provide password", 403)

    # Query database for username
    user = User.query.filter_by(username=request.form.get("username")).first()

    # Ensure username exists and password is correct
    if not user:
        return apology("User does not exist", 403)

    if not check_password_hash(user.password, request.form.get("password")):
        return apology("Invalid username and/or password", 403)

    # Remember which user has logged in
    session["user_id"] = user.id

    # Redirect user to home page
    return redirect("/")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User must reach route via POST, this ensures that
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username")
    # if name is already taken or blank return apology
    if not username:
        return apology("Username must have characters")
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return apology("Username already taken")

    # ask for password and confirmation
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")
    if not password or not confirmation:
        return apology("Password must not be blank")

    # password cannot be blank or type-mistake returns apology
    if password != confirmation:
        return apology("Password and confirmation not identical")

    hashed_password = generate_password_hash(password)

    # Insert the new user into the database
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    session["user_id"] = new_user.id

    # Redirect user to home page or login page
    return redirect("/")

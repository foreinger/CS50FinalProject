import os

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///budget.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # current user
    user = session["user_id"]

    # add budget list to session
    session["budget_list"] = db.execute("SELECT * FROM income WHERE user_id=:user", user=user)

    # if budget list still empty
    if not session['budget_list']:
        # invite user to enter revenue
        return redirect("/income")
    elif request.args.get("budget_id") != None:
        # user selected a specific budget list
        session["current_income"] = request.args.get("budget_id")
    elif session["current_income"] == "":
        # loading the last budget sheet
        session["current_income"] = session["budget_list"][-1]['id']

    # current balance
    session["balance"] = db.execute("SELECT cash FROM income WHERE user_id=:user AND  id=:current",
                                    user=user, current=session["current_income"])[0]['cash']

    # current budget list
    table_1 = db.execute("SELECT * FROM items WHERE income_id=:current_income AND num_table=1",
                         current_income=session["current_income"])
    table_2 = db.execute("SELECT * FROM items WHERE income_id=:current_income AND num_table=2",
                         current_income=session["current_income"])
    table_3 = db.execute("SELECT * FROM items WHERE income_id=:current_income AND num_table=3",
                         current_income=session["current_income"])
    table_4 = db.execute("SELECT * FROM items WHERE income_id=:current_income AND num_table=4",
                         current_income=session["current_income"])

    # preparing data for sending to user
    tables = [table_1, table_2, table_3, table_4]

    # tables names
    tab_names = ["Spending", "Savings", "Emergency case", "Loaned"]

    # add empty tables if user have not any one
    for i in range(len(tables)):
        if tables[i] == []:
            tables[i] = [{"num_table": i + 1}]
    # display current table
    return render_template("index.html", tables=tables, tab_names=tab_names)


@app.route("/income", methods=["GET", "POST"])
@login_required
def income():
    """ Inpute current income"""

    if request.method == "GET":
        # income entry page
        return render_template("income.html")
    else:
        # data request for the inputed income
        income = int(request.form.get("income"))

        # chek input
        if not income:
            return apology("input field is emtpy", 400)
        if income < 0:
            return apology("income can not be negative", 400)

        # current user
        user = session["user_id"]

        # update history
        db.execute("""INSERT INTO income (user_id, cash)
                   VALUES (:user, :cash)""", user=user, cash=income)

        # save current income in session
        session["current_income"] = db.execute("SELECT id FROM income WHERE user_id=:user", user=user)[-1]['id']

        # Redirect user to home page
        return redirect("/")


@app.route("/newItem", methods=["POST"])
@login_required
def newItem():
    """Add new item to budget"""

    # data request to the form
    item = request.values.get('item')
    cash = int(request.values.get('cash'))
    table = int(request.values.get('table')[-1])

    # current user
    user, current_income = session['user_id'], session['current_income']

    # update income
    db.execute("UPDATE income SET cash = cash - :item_cash WHERE id=:current_income",
               item_cash=cash, current_income=current_income)

    # update items
    db.execute("""INSERT INTO items (income_id, usr_id, comment, i_cash, num_table)
               VALUES (:income_id, :usr_id, :comment, :i_cash, :num_table)""", income_id=current_income, comment=item,
               usr_id=user, i_cash=cash, num_table=table)

    # if there is no such line in the table then create it
    result = db.execute(
        "SELECT item_id, cash FROM items LEFT JOIN income ON items.income_id=income.id WHERE income_id=:current_income", current_income=current_income)

    # Redirect user to home page
    return jsonify(result[-1])


@app.route("/delete_item", methods=["POST"])
@login_required
def delete_item():
    """Delete selected item"""
    # current user
    user, current_income = session['user_id'], session['current_income']

    # inputed value of stocks
    item_id = request.values.get("id")
    cash = request.values.get("cash")

    # update the account
    db.execute("UPDATE income SET cash = cash + :item_cash WHERE id=:current_income AND user_id=:user",
               item_cash=cash, current_income=current_income, user=user)

    # delete item
    db.execute("DELETE FROM items WHERE item_id=:item_id AND usr_id=:user", item_id=item_id, user=user)

    # prepare current balance for sending
    result = db.execute("SELECT cash FROM income WHERE id=:current_income", current_income=current_income)[0]

    # sending data to user
    return jsonify(result)


@app.route("/edit_item", methods=["POST"])
@login_required
def edit_item():
    """Edit selected item"""
    # current user
    user, current_income = session['user_id'], session['current_income']

    # received value of stocks
    item_id = request.values.get("id")
    oldVal = request.values.get("oldVal")
    newVal = request.values.get("newVal")
    col = request.values.get("col")[-1]

    # edit first or second cell
    if col == "1":
        db.execute("UPDATE items SET comment = :comment WHERE item_id=:item_id AND usr_id=:user",
                   comment=newVal, item_id=item_id, user=user)
    elif col == "2":
        db.execute("UPDATE items SET i_cash = :value WHERE item_id=:item_id AND usr_id=:user",
                   item_id=item_id, value=int(newVal), user=user)
        db.execute("UPDATE income SET cash = cash + :edit WHERE id=:current_income AND user_id=:user",
                   edit=int(oldVal)-int(newVal), current_income=current_income, user=user)

    # prepare current balance for sending
    result = db.execute("SELECT cash FROM income WHERE id=:current_income", current_income=current_income)[0]

    # sending data to user
    return jsonify(result)


@app.route("/done_or_not", methods=["POST"])
@login_required
def done_or_not():
    """Add new item to budget"""

    # data request to the form
    item_id = request.values.get("id")
    answer = request.values.get("answer")

    # current user
    user, current_income = session['user_id'], session['current_income']

    # update items
    db.execute("UPDATE items SET completed = :answer WHERE item_id=:item_id AND usr_id=:user",
               answer=answer, item_id=item_id, user=user)

    # prepare current item_id for sending
    result = {'key': item_id}

    # Redirect user to home page
    return jsonify(result)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"], session["name"] = rows[0]['id'], rows[0]["username"]

        current_income = db.execute("SELECT id, cash FROM income WHERE user_id=:user", user=rows[0]['id'])

        if current_income == []:
            return redirect("/income")
        else:
            session["current_income"] = current_income[-1]['id']
            session["balance"] = current_income[-1]['cash']

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


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
    if request.method == "POST":

        if not db.execute("INSERT INTO users (username, hash) VALUES (:username, :passhash)", username=request.form.get("username"),
                          passhash=generate_password_hash(request.form.get("password"))):
            return apology("Something went wrong", 400)

        # Remember which user has registered
        s = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))[0]
        session["user_id"], session["name"] = s['id'], s["username"]

        # Redirect user to home page
        return redirect("/intro")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/intro")
def intro():
    """Show intro page"""

    return render_template("intro.html")


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    """Log user in"""

    # User reached route via POST
    if request.method == "POST":

        # waiting for an answer
        if request.form["question"] == "yes":

            # current user
            user = session["user_id"]

            # remove current user from all tables
            db.execute("DELETE FROM users WHERE id = :user", user=user)

            # Forget any user_id
            session.clear()

            # return to the strt page
            return redirect("/")

        # Ensure password was submitted
        elif request.form["question"] == "no":
            return redirect("/")

    else:
        return render_template("delete.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

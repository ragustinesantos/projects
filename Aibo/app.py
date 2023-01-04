from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from functions import login_required, cad, error

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Session time limit and storage
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///project.db")

# Date and Time variables
now = datetime.now()
year = now.strftime("%Y")
month = now.strftime("%m")
day = now.strftime("%d")
time = now.strftime ("%H:%M:%S")

# Register filter for use in web page
app.jinja_env.filters["cad"] = cad


@app.route("/")
@login_required
def index():

   # Retrieve user id
   user = session["user_id"]

   # Set default value of total to 0
   total = 0

   # Populate type of transactions
   type = db.execute("SELECT * FROM transaction_type")

   # Retrieve current cart for the session
   cart = db.execute("SELECT * FROM session WHERE user_id = ?", user)
   countCart = int(db.execute("SELECT COUNT(*) FROM session WHERE user_id = ?", user)[0]["COUNT(*)"])

   # IF there is an entry present in session table, retrieve total value of total column for current cart
   if countCart > 0:
      total = float(db.execute("SELECT SUM(total) FROM session WHERE user_id = ?", user)[0]["SUM(total)"])

   return render_template("index.html", type=type, cart=cart, total=total, cad=cad)


@app.route("/add", methods=["POST"])
@login_required
def add():

   # Retrieve user id
   user = session["user_id"]

   # IF item is empty, return error
   if not request.form.get("newItem"):
      return error("Please enter an item")

   # IF quantity is empty, return error
   if not request.form.get("newQuantity") or float(request.form.get("newQuantity")) == 0:
      return error("Please enter a valid quantity")

   # IF price is empty, return error
   if not request.form.get("newPrice") or float(request.form.get("newPrice")) == 0:
      return error("Please enter a valid price")

   # ELSE if all fields are valid, retrieve item information from form
   type = request.form.get("newType")
   item = request.form.get("newItem")
   quantity = request.form.get("newQuantity")
   price = request.form.get("newPrice")

   # Compute for total purchase value
   total = float(quantity) * float(price)

   # INSERT item details INTO current shopping session's database
   db.execute("INSERT INTO session (user_id, year, month, day, item, price, quantity, total, type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            user, year, month, day, item, price, quantity, total, type)

   # REDIRECT to /
   return redirect("/")


@app.route("/save", methods=["POST"])
@login_required
def save():

   # Retrieve user id
   user = session["user_id"]

   # INSERT all items recorded in the current shopping session to the database
   db.execute("INSERT INTO savedData SELECT * FROM session WHERE user_id = ?", user)

   # Clear current session
   db.execute("DELETE FROM session WHERE user_id = ?", user)

   # Redirect to /
   return redirect("/")


@app.route("/delete", methods=["POST"])
@login_required
def delete():

   # Retrieve user id
   user = session["user_id"]

   # Store transaction number of item to be deleted in a variable
   deleteItem = request.form.get("deleteItem")

   # DELETE row of item
   db.execute("DELETE FROM session WHERE user_id = ? and trans_number = ?", user, deleteItem)

   # REDIRECT to /
   return redirect("/")


@app.route("/deleteSummary", methods=["POST"])
@login_required
def deleteSummary():

   # Retrieve user id
   user = session["user_id"]

   # Store transaction number of item to be deleted in a variable
   trans = request.form.get("deleteTrans")

   # DELETE row of item
   db.execute("DELETE FROM savedData WHERE user_id = ? and trans_number = ?", user, trans)

   # REDIRECT to /summary
   return redirect("/summary")


@app.route("/editSummary", methods=["POST"])
@login_required
def editSummary():

   # Retrieve user id
   user = session["user_id"]

   # Store item details to be edited in variables
   trans = request.form.get("editTrans")
   item = request.form.get("item")
   quantity = request.form.get("quantity")
   price = request.form.get("price")
   total = float(quantity) * float(price)

   # UPDATE row of edited item with new details
   db.execute("UPDATE savedData SET item = ?, quantity = ?, price = ?, total = ? WHERE user_id = ? AND trans_number = ?", item, quantity, price, total, user, trans)

   # REDIRECT to /summary
   return redirect("/summary")


@app.route("/reset", methods=["POST"])
@login_required
def reset():

   # Retrieve user id
   user = session["user_id"]

   # Clear all rows from session
   db.execute("DELETE FROM session WHERE user_id = ?", user)

   # REDIRECT to /
   return redirect("/")


@app.route("/summary", methods=["GET", "POST"])
@login_required
def summary():

   # Retrieve user id
   user = session["user_id"]

   # Define year and month as currentYear and currentMonth
   currentYear = year
   currentMonth = month

   # Store category names in variables
   grocery = "Grocery"
   bills = "Bills"
   misc = "Miscellaneous"
   food = "Food"
   transpo = "Transportation"

   # Create a list of month numbers and years
   monthList = list(range(1,13))
   yearList = list(range(2020, int(currentYear)+1))

   # IF user reched route via POST
   if request.method == "POST":

      # Store input year and month in variables
      selectionYear = int(request.form.get("year"))
      selectionMonth = int(request.form.get("month"))

      # Get the SUM of total column per category for the selected month and year
      sumTotal = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND month = ? AND year = ?", user, selectionMonth, selectionYear)[0]["COALESCE(SUM(total),0)"])
      sumGrocery = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, grocery, selectionMonth, selectionYear)[0]["COALESCE(SUM(total),0)"])
      sumBills = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, bills, selectionMonth, selectionYear)[0]["COALESCE(SUM(total),0)"])
      sumMisc = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, misc, selectionMonth, selectionYear)[0]["COALESCE(SUM(total),0)"])
      sumFood = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, food, selectionMonth, selectionYear)[0]["COALESCE(SUM(total),0)"])
      sumTranspo = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, transpo, selectionMonth, selectionYear)[0]["COALESCE(SUM(total),0)"])

      # Retrieve tables of all categories of the user per transaction type from current month of the current year
      totalSelection = db.execute("SELECT * FROM savedData WHERE user_id = ? AND month = ? AND year = ? ORDER BY year DESC, month DESC, day DESC, trans_number DESC", user, selectionMonth, selectionYear)
      grocerySelection = db.execute("SELECT * FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ? ORDER BY year DESC, month DESC, day DESC, trans_number DESC", user, grocery, selectionMonth, selectionYear)
      billsSelection = db.execute("SELECT * FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ? ORDER BY year DESC, month DESC, day DESC, trans_number DESC", user, bills, selectionMonth, selectionYear)
      miscSelection = db.execute("SELECT * FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ? ORDER BY year DESC, month DESC, day DESC, trans_number DESC", user, misc, selectionMonth, selectionYear)
      foodSelection = db.execute("SELECT * FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ? ORDER BY year DESC, month DESC, day DESC, trans_number DESC", user, food, selectionMonth, selectionYear)
      transpoSelection = db.execute("SELECT * FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ? ORDER BY year DESC, month DESC, day DESC, trans_number DESC", user, transpo, selectionMonth, selectionYear)

      return render_template("summary.html", displayYear=selectionYear, displayMonth=selectionMonth, sumTotal=sumTotal, sumGrocery=sumGrocery, sumBills=sumBills, sumMisc=sumMisc, sumFood=sumFood, sumTranspo=sumTranspo,
                              totalSelection=totalSelection, grocerySelection=grocerySelection, billsSelection=billsSelection, miscSelection=miscSelection, foodSelection=foodSelection, transpoSelection=transpoSelection,
                              monthList=monthList, yearList=yearList, cad=cad)

   # ELSE if the user reched route via GET
   else:

      # Get the SUM of total column per category for the current month and year
      sumTotal = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ?", user)[0]["COALESCE(SUM(total),0)"])
      sumGrocery = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ?", user, grocery)[0]["COALESCE(SUM(total),0)"])
      sumBills = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ?", user, bills)[0]["COALESCE(SUM(total),0)"])
      sumMisc = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ?", user, misc)[0]["COALESCE(SUM(total),0)"])
      sumFood = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ?", user, food)[0]["COALESCE(SUM(total),0)"])
      sumTranspo = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ?", user, transpo)[0]["COALESCE(SUM(total),0)"])

      # Retrieve tables of all transactions of the user per category from current month of the current year
      totalSelection = db.execute("SELECT * FROM savedData WHERE user_id = ? ORDER BY year DESC, month DESC, day DESC, trans_number DESC", user)
      grocerySelection = db.execute("SELECT * FROM savedData WHERE user_id = ? AND type = ? ORDER BY year DESC, month DESC, day DESC, trans_number DESC", user, grocery)
      billsSelection = db.execute("SELECT * FROM savedData WHERE user_id = ? AND type = ? ORDER BY year DESC, month DESC, day DESC, trans_number DESC", user, bills)
      miscSelection = db.execute("SELECT * FROM savedData WHERE user_id = ? AND type = ? ORDER BY year DESC, month DESC, day DESC, trans_number DESC", user, misc)
      foodSelection = db.execute("SELECT * FROM savedData WHERE user_id = ? AND type = ? ORDER BY year DESC, month DESC, day DESC, trans_number DESC", user, food)
      transpoSelection = db.execute("SELECT * FROM savedData WHERE user_id = ? AND type = ? ORDER BY year DESC, month DESC, day DESC, trans_number DESC", user, transpo)

      return render_template("summary.html", displayYear=currentYear, displayMonth=currentMonth, sumTotal=sumTotal, sumGrocery=sumGrocery, sumBills=sumBills, sumMisc=sumMisc, sumFood=sumFood, sumTranspo=sumTranspo,
                              totalSelection=totalSelection, grocerySelection=grocerySelection, billsSelection=billsSelection, miscSelection=miscSelection, foodSelection=foodSelection, transpoSelection=transpoSelection,
                              monthList=monthList, yearList=yearList, cad=cad)


@app.route("/login", methods=["GET", "POST"])
def login():

   # Clear session data
   session.clear()

   # IF user reached route via POST
   if request.method == "POST":

      if not request.form.get("username"):
         return error("Please enter a valid username")

      if not request.form.get("password"):
         return error("Please enter a valid username")

      # Query database for username
      user = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

      # Ensure username exists and password is correct
      if len(user) != 1 or not check_password_hash(user[0]["password"], request.form.get("password")):
         return error("Invalid username and/or password")

      # Remember which user has logged in
      session["user_id"] = user[0]["id"]

      # Redirect user to home page
      return redirect("/")

   # ELSE if user reached route via GET
   else:
      return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

   # IF user reached route via POST
   if request.method == "POST":

      # Store input username, password and password confirmation in variables
      username = request.form.get("username")
      password = request.form.get("password")
      confirmation = request.form.get("confirmation")

      # IF username input is empty, return error
      if not username:
         return error("Please provide a valid username")

      # ELSE IF username is able to be drawn from the list of users, return error
      elif int(db.execute("SELECT COUNT(*) FROM users WHERE username = ?", username)[0]["COUNT(*)"]) > 0:
         return error("Username already exists")

      # ELSE IF password field is empty or input is less than 8 characters, return error
      elif not password or len(password) < 8:
         return error("Please provide a valid passowrd")

      # ELSE IF password confirmation does not match password input, return error
      elif password != confirmation:
         return error("Password does not match")

      # ELSE generate password hash then store username and password inside users table. Return success page afterwards.
      else:
         pwhash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
         db.execute("INSERT INTO users (username, password) VALUES(?, ?)", username, pwhash)
         return redirect("/login")

   # ELSE if user reached route via GET
   else:
      return render_template("register.html")


@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/budget", methods=["GET", "POST"])
@login_required
def budget():

   # Retrieve user id
   user = session["user_id"]

   # Define year and month as currentYear and currentMonth
   currentYear = year
   currentMonth = month

   # Create a list of month numbers and years
   monthList = list(range(1,13))
   yearList = list(range(2020, int(currentYear)+1))

   # Store category names in variables
   grocery = "Grocery"
   bills = "Bills"
   misc = "Miscellaneous"
   food = "Food"
   transpo = "Transportation"

   # If there is no budget data for the current date, insert a new row in the budget table
   countBudget = float(db.execute("SELECT COUNT(*) FROM budget WHERE user_id = ? AND month = ? AND year = ?", user, currentMonth, currentYear)[0]["COUNT(*)"])
   if countBudget == 0:
      db.execute("INSERT INTO budget (user_id, year, month) VALUES (?, ?, ?)", user, currentYear, currentMonth)

   # Retrieve total expense data
   summaryTotal = db.execute("SELECT DISTINCT year, month, COALESCE(SUM(total),0) AS total FROM savedData WHERE user_id = ? ORDER BY year, month", user)

   # IF user reached route via POST
   if request.method == "POST":

      if not request.form.get("year") or not request.form.get("month"):
         return error("Please select a valid date")

      # Store selected date in variables
      selectionYear = int(request.form.get("year"))
      selectionMonth = int(request.form.get("month"))

      # If there is no budget data for the current date, insert a new row in the budget table
      countBudget = int(db.execute("SELECT COUNT(*) FROM budget WHERE user_id = ? AND month = ? AND year = ?", user, selectionMonth, selectionYear)[0]["COUNT(*)"])
      if countBudget < 1:
         db.execute("INSERT INTO budget (user_id, year, month) VALUES (?, ?, ?)", user, selectionYear, selectionMonth)

      # Retrieve set budget for the date selected
      setBudget = float(db.execute("SELECT budget FROM budget WHERE user_id = ? AND month = ? AND year = ?", user, selectionMonth, selectionYear)[0]["budget"])

      # Get the SUM of total column per category for the selected month and year
      sumTotal = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND month = ? AND year = ?", user, selectionMonth, selectionYear)[0]["COALESCE(SUM(total),0)"])
      sumGrocery = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, grocery, selectionMonth, selectionYear)[0]["COALESCE(SUM(total),0)"])
      sumBills = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, bills, selectionMonth, selectionYear)[0]["COALESCE(SUM(total),0)"])
      sumMisc = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, misc, selectionMonth, selectionYear)[0]["COALESCE(SUM(total),0)"])
      sumFood = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, food, selectionMonth, selectionYear)[0]["COALESCE(SUM(total),0)"])
      sumTranspo = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, transpo, selectionMonth, selectionYear)[0]["COALESCE(SUM(total),0)"])

      # Update expense column with current total expense data for the date selected
      db.execute("UPDATE budget SET expense = ? WHERE user_id = ? AND month = ? AND year = ?", sumTotal, user, selectionMonth, selectionYear)

      # Retrieve budget table
      summaryBudget = db.execute("SELECT * FROM budget WHERE user_id = ? ORDER BY year DESC, month DESC", user)

      # Get the remaining budget by subtracting the sum of total expenses for the month of the selected year by the setBudget for the same date
      remainingBudget = float(max(int(setBudget-sumTotal),0))

      return render_template("budget.html", monthList=monthList, yearList=yearList, month=selectionMonth, year=selectionYear, setBudget=setBudget, sumTotal=sumTotal, sumGrocery=sumGrocery, sumBills=sumBills, sumMisc=sumMisc,
                              sumFood=sumFood, sumTranspo=sumTranspo, remainingBudget=remainingBudget, summaryBudget=summaryBudget, summaryTotal=summaryTotal, cad=cad)

   # ELSE if user reached route via GET
   else:

      # Retrieve set budget for the current date
      setBudget = float(db.execute("SELECT budget FROM budget WHERE user_id = ? AND month = ? AND year = ?", user, currentMonth, currentYear)[0]["budget"])

      # Get the SUM of total column per category for the selected month and year
      sumTotal = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND month = ? AND year = ?", user, currentMonth, currentYear)[0]["COALESCE(SUM(total),0)"])
      sumGrocery = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, grocery , currentMonth, currentYear)[0]["COALESCE(SUM(total),0)"])
      sumBills = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, bills , currentMonth, currentYear)[0]["COALESCE(SUM(total),0)"])
      sumMisc = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, misc , currentMonth, currentYear)[0]["COALESCE(SUM(total),0)"])
      sumFood = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, food , currentMonth, currentYear)[0]["COALESCE(SUM(total),0)"])
      sumTranspo = float(db.execute("SELECT COALESCE(SUM(total),0) FROM savedData WHERE user_id = ? AND type = ? AND month = ? AND year = ?", user, transpo , currentMonth, currentYear)[0]["COALESCE(SUM(total),0)"])

      # Update expense column with current total expense data for the current date
      db.execute("UPDATE budget SET expense = ? WHERE user_id = ? AND month = ? AND year = ?", sumTotal, user, currentMonth, currentYear)

      # Retrieve budget table
      summaryBudget = db.execute("SELECT * FROM budget WHERE user_id = ? ORDER BY year DESC, month DESC", user)

      # Get the remaining budget by subtracting the sum of total expenses for the month of the selected year by the setBudget for the same date
      remainingBudget = float(max(int(setBudget-sumTotal),0))

      return render_template("budget.html", monthList=monthList, yearList=yearList, month=currentMonth, year=currentYear, setBudget=setBudget, sumTotal=sumTotal, sumGrocery=sumGrocery, sumBills=sumBills, sumMisc=sumMisc, sumFood=sumFood, sumTranspo=sumTranspo,
                              remainingBudget=remainingBudget, summaryBudget=summaryBudget, summaryTotal=summaryTotal, cad=cad)


@app.route("/set", methods=["POST"])
def set():

   user = session["user_id"]

   # IF no budget is provided, return error
   if not request.form.get("budget"):
      return error("Please provide a valid number")

   # IF no date is provided, return error
   if not request.form.get("year") or not request.form.get("month"):
      return error("Please provide a valid date")

   # Store budget, selected year and month in variables
   budget = float(request.form.get("budget"))
   selectionYear = request.form.get("year")
   selectionMonth = request.form.get("month")

   # If there is no budget data for the current date, insert a new row in the budget table
   countBudget = int(db.execute("SELECT COUNT(*) FROM budget WHERE user_id = ? AND month = ? AND year = ?", user, selectionMonth, selectionYear)[0]["COUNT(*)"])
   if countBudget < 1:
      db.execute("INSERT INTO budget (user_id, year, month) VALUES (?, ?, ?)", user, selectionYear, selectionMonth)

   # UPDATE budget table with the budget set for the date provided
   db.execute("UPDATE budget SET budget = ? WHERE user_id = ? AND month = ? AND year = ?", budget, user, selectionMonth, selectionYear)

   # Redirect to /budget
   return redirect("/budget")

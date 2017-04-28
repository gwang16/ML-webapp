from flask import Flask, render_template, request, redirect, url_for, session
from cs50 import SQL # easier to execute SQL commands
from utility import lookup, quote, buy, sell, execute, strategy1, apology, login_required, usd
import pandas as pd
from passlib.context import CryptContext # password hashing
from flask_session import Session # track log in status
from tempfile import gettempdir 

app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# jinja customization
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure hash algorithm
pwd_context = CryptContext(
                schemes=["pbkdf2_sha256", "des_crypt"],
                deprecated="auto",
            )


# configure CS50 Library to use SQLite database
db = SQL("sqlite:///3.db/finance.db")

# import data
df = pd.read_csv('./1.data/AAPL.csv', parse_dates = True, index_col = 0) 
df['100ma'] = df['Adj Close'].rolling(window = 100, min_periods = 0).mean() 


@app.route("/")
@login_required
def index():
    portfolio = db.execute("SELECT symbol, SUM(shares) AS shares FROM history WHERE user_id = :id GROUP BY 1 ORDER BY 1", 
            id=session["user_id"])
    cash = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])[0].get("cash")
    
    for stock in portfolio:
        symbol = stock.get("symbol").upper()
        stock["name"] = lookup(symbol).get("name")
        stock["price"] = lookup(symbol).get("price")
        stock["total"] = float(stock["shares"]) * stock["price"]
    
    running_total = float(cash) + sum(stock["total"] for stock in portfolio)
    
    return render_template("index.html", portfolio = portfolio, cash = cash, total = running_total)

@app.route('/strats', methods=["GET", "POST"])
@login_required
def strats():
    """Execute various satelite strategies"""
    if request.method == "POST":
        execute(strategy1(df))
        return redirect(url_for("index"))
    else:
        return render_template("strats.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    
    hist = db.execute("SELECT * FROM history where user_id = :user_id", user_id=session["user_id"])
    return render_template("history.html", history = hist)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # check for username input
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        if not request.form.get("username"):
            return apology("username cannot be blank")
        elif len(rows) == 1:
            return apology("username already exists")
        
        # check for password input
        if not request.form.get("password"):
            return apology("password cannot be blank")
        elif request.form.get("password") != request.form.get("password_r"):
            return apology("passwords do not match")
        
        # insert username and hashed password into database
        db.execute("INSERT INTO users (username, hash) VALUES(:username, :hashed)", 
            username=request.form.get("username"), hashed=pwd_context.hash(request.form.get("password")))
        return redirect(url_for("index"))
            
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


if __name__ == '__main__':
    app.run(debug=True)
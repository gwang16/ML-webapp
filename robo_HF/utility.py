from cs50 import SQL
import csv
import urllib.request

from flask import redirect, render_template, request, session, url_for
from functools import wraps

db = SQL("sqlite:///3.db/finance.db")
# session = {'user_id':4}

def apology(top="", bottom=""):
    """Renders message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
            ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=escape(top), bottom=escape(bottom))

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def usd(value):
    """Formats value as USD."""
    return "${:,.2f}".format(value)

def lookup(symbol):
    """Look up quote for symbol."""

    # reject symbol if it starts with caret
    if symbol.startswith("^"):
        return None

    # reject symbol if it contains comma
    if "," in symbol:
        return None

    # query Yahoo for quote
    # http://stackoverflow.com/a/21351911
    try:
        url = "http://download.finance.yahoo.com/d/quotes.csv?f=snl1&s={}".format(symbol)
        webpage = urllib.request.urlopen(url)
        datareader = csv.reader(webpage.read().decode("utf-8").splitlines())
        row = next(datareader)
    except:
        return None

    # ensure stock exists
    try:
        price = float(row[2])
    except:
        return None

    # return stock's name (as a str), price (as a float), and (uppercased) symbol (as a str)
    return {
        "name": row[1],
        "price": price,
        "ticker": row[0].upper()
    }

def quote(ticker):
    return lookup(ticker).get("price")

def sell(ticker, shares):
    # Check for shares in portfolio
    portfolio = db.execute("SELECT symbol, SUM(shares) AS shares FROM history WHERE user_id = :id GROUP BY 1 HAVING symbol = :symbol", 
        id=session["user_id"], symbol = ticker.upper())
    if len(portfolio) < 1:
        return None
    if float(shares) > portfolio[0].get("shares"):
        return None
    # Current stock price
    price = lookup(ticker).get("price")
    # Amount in bank account
    cash = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])[0].get("cash")
    # Store who, what, how many, how much, when
    db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES(:user_id, :symbol, :shares, :price)", 
                user_id = session["user_id"], symbol = ticker.upper(), 
                shares = -1 * float(shares), price = price)
    # Add cash to account
    db.execute("UPDATE 'users' SET cash = :cash where id = :id", 
            cash = float(cash) + float(price) * float(shares), id = session["user_id"])
    return "Sold {} shares of {}, at price {}. Remaining balance is {}".format(shares, ticker, price, cash)

def buy(ticker, shares):
    # Current stock price
    price = lookup(ticker).get("price")
    # Amount in bank account
    cash = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])[0].get("cash")
    # Check affordability
    if float(price) * float(shares) > float(cash):
        return "you are trying to buy {} shares of {}, which costs {}, but you only have {}".format(shares, ticker, price, cash)
    # Store who, what, how many, how much, when
    db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES(:user_id, :ticker, :shares, :price)", 
                user_id = session["user_id"], ticker = ticker.upper(), 
                shares = shares, price = price)
    # Reduce cash
    db.execute("UPDATE 'users' SET cash = :cash where id = :id", 
            cash = float(cash) - float(price) * float(shares), id = session["user_id"])
    return "Bought {} shares of {}, at price {}. Remaining balance is {}".format(shares, ticker, price, cash)

def execute(strategy):
    if strategy.get("position") == "buy":
        buy(strategy.get("ticker"), strategy.get("shares"))
    if strategy.get("position") == "sell":
        sell(strategy.get("ticker"), strategy.get("shares"))

def strategy1(df):
    if df['Adj Close'][len(df)-1] > df['100ma'][len(df)-1]:
        position = "buy"
    if df['Adj Close'][len(df)-1] < df['100ma'][len(df)-1]:
        position = "sell"

    # ignore order type for now
    return {
        "ticker": "AAPL",
        "position": position,
        "shares": 1
    }        



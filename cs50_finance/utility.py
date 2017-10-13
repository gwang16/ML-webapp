from cs50 import SQL
from helpers import *

db = SQL("sqlite:///finance.db")

def sell(ticker, shares):
    # Mimics the sell function in application.py
    portfolio = db.execute("SELECT symbol, SUM(shares) AS shares FROM history WHERE user_id = :id GROUP BY 1 HAVING symbol = :symbol", 
        id=session["user_id"], symbol = ticker.upper())
    if len(portfolio) < 1:
        return None
    if float(shares) > portfolio[0].get("shares"):
        return None
    
    price = lookup(ticker).get("price")
    
    cash = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])[0].get("cash")
    
    db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES(:user_id, :symbol, :shares, :price)", 
                user_id = session["user_id"], symbol = ticker.upper(), 
                shares = -1 * float(shares), price = price)
    
    db.execute("UPDATE 'users' SET cash = :cash where id = :id", 
            cash = float(cash) + float(price) * float(shares), id = session["user_id"])
    return "Sold {} shares of {}, at price {}. Remaining balance is {}".format(shares, ticker, price, cash)

def buy(ticker, shares):
    # Mimics the buy function in application.py
    price = lookup(ticker).get("price")
    
    cash = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])[0].get("cash")
    
    if float(price) * float(shares) > float(cash):
        return "you are trying to buy {} shares of {}, which costs {}, but you only have {}".format(shares, ticker, price, cash)
    
    db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES(:user_id, :ticker, :shares, :price)", 
                user_id = session["user_id"], ticker = ticker.upper(), 
                shares = shares, price = price)
    
    db.execute("UPDATE 'users' SET cash = :cash where id = :id", 
            cash = float(cash) - float(price) * float(shares), id = session["user_id"])
    return "Bought {} shares of {}, at price {}. Remaining balance is {}".format(shares, ticker, price, cash)

def execute(strategy):
    # iterate through each strat (dictionary) in strategy (list of dictionaries)
    for strat in strategy:
        if strat.get("position") == "buy":
            buy(strat.get("ticker"), strat.get("shares"))
        elif strat.get("position") == "sell":
            sell(strat.get("ticker"), strat.get("shares"))
        else: pass

def strategy1(df):
    # momentum based strategy
    # If dataset df is updated everyday, then this strategy purchases a share of AAPL if close "crosses" the 100ma
    df['100ma'] = df['AAPL'].rolling(window = 100, min_periods = 0).mean()
    if df['AAPL'][len(df)-1] > df['100ma'][len(df)-1] and df['AAPL'][len(df)-2] < df['100ma'][len(df)-2]:
        position = "buy"
    elif df['AAPL'][len(df)-1] < df['100ma'][len(df)-1] and df['AAPL'][len(df)-2] > df['100ma'][len(df)-2]:
        position = "sell"
    else: position = "hold"

    # ignore order type for now
    # return a list of dictionary
    print(position)
    print(df['AAPL'][len(df)-3], df['100ma'][len(df)-3])
    print(df['AAPL'][len(df)-2], df['100ma'][len(df)-2])
    print(df['AAPL'][len(df)-1], df['100ma'][len(df)-1])
    return [{
        "ticker": "AAPL",
        "position": position,
        "shares": 1
    }] 

def strategy2(df):
    # multiple MA strategy - on all components of S&P
    strategy = []
    for i in range(len(df.columns)):
        df['100ma'] = df.iloc[:,i].rolling(window = 100, min_periods = 0).mean()
        if df.iloc[len(df)-1, i] > df['100ma'][len(df)-1] and df.iloc[len(df)-2,i] < df['100ma'][len(df)-2]:
            position = "buy"
        elif df.iloc[len(df)-1, i] < df['100ma'][len(df)-1] and df.iloc[len(df)-2, i] > df['100ma'][len(df)-2]:
            position = "sell"
        else: position = "hold"
        strategy.append({
            "ticker": df.columns[i],
            "position": position,
            "shares": 1
        })
    print(strategy)
    return strategy

def strategy3(df):
    # value based strategy
    # buy lowest P/E ratio, sell highest P/E ratio
    last_price = df.iloc[len(df)-1,:]
    # ---- need to download earnings data -----
    forward_earnings = 1
    pe_ratio = last_price / forward_earnings
    pe_ratio.sort_values(inplace=True)
    labels = pe_ratio.index.values
    # buy bottom 3 and short top 3
    strategy = []
    for i in range(len(pe_ratio)):

        # purchase top 3
        if i in range(0,3):
            strategy.append({
                "ticker": labels[i],
                "position": "buy",
                "shares": 1
                })

        # sell bottom 3
        elif i in range(len(labels)-3,len(labels)):
            strategy.append({
                "ticker": labels[i],
                "position": "sell",
                "shares": 1
                })
            
        else:
            strategy.append({
                "ticker": labels[i],
                "position": "hold",
                "shares": 1
                })
    print(strategy)        
    return strategy

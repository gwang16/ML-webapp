import csv
import urllib.request

from flask import redirect, render_template, request, session, url_for
from functools import wraps



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
        "symbol": row[0].upper()
    }

def usd(value):
    """Formats value as USD."""
    return "${:,.2f}".format(value)



import bs4 as bs # parses html
import pickle # save any python object
import requests # send GET requests to webpages

import datetime as dt
import os 
import pandas as pd
import pandas_datareader.data as web

import matplotlib.pyplot as plt
import matplotlib.style as style

import numpy as np

def save_sp500_tickers():
    # get sourcecode from webpages
    resp = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    
    # use bs to parse html, specifically find table object 
    soup = bs.BeautifulSoup(resp.text, "html.parser")
    table = soup.find('table', {'class':'wikitable sortable'})

    # for each row, save the ticker to a list
    tickers = []
    for row in table.findAll('tr')[1:]: # ignore first row (header)
        ticker = row.findAll('td')[0].text # ignore all but first column, the ticker
        mapping = str.maketrans(".","-") # wiki turns - in company names to . so this reverses the process
        ticker = ticker.translate(mapping)
        tickers.append(ticker)

    # cut down on population
    tickers = tickers[:50]

    # save tickers (a python list) to a pickle file
    with open('data/sp500tickers.pickle', 'wb') as f:
        pickle.dump(tickers, f)

    return tickers


def get_data_from_google(reload_sp500 = False):
    # check if require to re-download tickers from wiki
    if reload_sp500:
        tickers = save_sp500_tickers()
    # otherwise just read from the saved pickle file
    else:
        with open('data/sp500tickers.pickle', 'rb') as f:
            tickers = pickle.load(f)
    # create directory to save data
    if not os.path.exists('data/stock_dfs'):
        os.makedirs('data/stock_dfs')

    # grab data from yahoo api and save 
    start = dt.datetime(2001, 1, 1)
    end = dt.date.today()
    
    for ticker in tickers:
        print(ticker)
        if not os.path.exists('data/stock_dfs/{}.csv'.format(ticker)):
            df = web.DataReader(ticker, 'google', start, end)
            df.to_csv('data/stock_dfs/{}.csv'.format(ticker))
        else:
            print('Already have {}'.format(ticker))


def compile_data():
    
    # read ticker names from pickle object
    with open('data/sp500tickers.pickle', 'rb') as f:
        tickers = pickle.load(f)

    # create empty data frame object
    main_df = pd.DataFrame()

    # read price csv for each ticker, and combine closing price into one dataframe 
    for count,ticker in enumerate(tickers):
        df = pd.read_csv('data/stock_dfs/{}.csv'.format(ticker))
        df.set_index('Date', inplace = True)
        df.rename(columns = {'Close': ticker}, inplace = True)
        df.drop(['Open','High','Low','Volume'], 1, inplace = True)
        if main_df.empty:
            main_df = df
        else:
            main_df = main_df.join(df, how = 'outer')
        if count % 10 == 0:
            print(count)

    print(main_df.head())
    main_df.to_csv('data/sp500_joined_closes.csv')

def visualize_data():
    df = pd.read_csv('data/sp500_joined_closes.csv')
    # df['AAPL'].plot()
    # plt.show()

    df.set_index('Date', inplace = True)
    
    # calculate daily relative return
    df_ret = df.pct_change(periods = 1)

    # caculate correlation of return
    df_corr = df_ret.corr()
    print(df_corr.head())

    # create heatmap
    data = df_corr.values
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1) # 1 by 1, plot id # 1

    heatmap = ax.pcolor(data, cmap = plt.cm.RdYlGn) # plot color, cmap is a range from red to yellow to green
    fig.colorbar(heatmap) # legend
    ax.set_xticks(np.arange(data.shape[0]) + 0.5, minor = False) # add tick marks
    ax.set_yticks(np.arange(data.shape[1]) + 0.5, minor = False) 
    ax.invert_yaxis() # gap at the top of matplotlib 
    ax.xaxis.tick_top() # moves x-axis from bottom to top 

    column_labels = df_corr.columns # labels are company names
    row_labels = df_corr.index

    ax.set_xticklabels(column_labels) 
    ax.set_yticklabels(row_labels)
    plt.xticks(rotation = 90) # rotate x labels by 90 degrees
    heatmap.set_clim(-1, 1) # limit values from -1 to 1
    plt.tight_layout()
    plt.show()


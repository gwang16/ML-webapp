import numpy as np
import pandas as pd
import pickle

from collections import Counter

from sklearn import svm, cross_validation, neighbors
from sklearn.ensemble import VotingClassifier, RandomForestClassifier

def main():
	#process_data_for_labels('XOM')
	#extract_featureset('XOM')
	do_ml('BAC')


def process_data_for_labels(ticker):
	hm_days = 7
	df = pd.read_csv('sp500_joined_closes.csv', index_col = 0)
	tickers = df.columns.values.tolist() # column names
	#df.fillna(0, inplace = True) 

	# find TICKER_Xd returns for all tickers and days from 1 to 7
	for i in range(1, hm_days + 1):
		df['{}_{}d'.format(ticker, i)] = (df[ticker].shift(-i) - df[ticker] ) / df[ticker]

	df.fillna(0, inplace = True) # na to 0
	return tickers, df

# allows us to iterate through arguments
def buy_sell_hold(*args): 
	
	# pass in columns as parameters, take 1 row at a time 
	cols = [c for c in args]
	#requirement = 0.02
	requirement = 0.028

	# if the stock return exceeds requirement in any of the following n days, buy
	for col in cols:
		if col > requirement:
			return 1
		if col < -requirement:
			return -1
	return 0

def extract_featureset(ticker):
	tickers, df = process_data_for_labels(ticker)
	hm_days = 7

	# create target variable column, that passes 1 to 7 day returns through the buy_sell_hold function
	df['{}_target'.format(ticker)] = list(map(buy_sell_hold, 
												*[df['{}_{}d'.format(ticker, i)] for i in range(1, hm_days + 1)]
												))

	vals = df['{}_target'.format(ticker)].values.tolist()
	str_vals = [str(i) for i in vals]
	print('Data spread:', Counter(str_vals)) # returns distribution of buy, sell and hold

	df.fillna(0, inplace = True) # replace na with 0 
	df = df.replace([np.inf, -np.inf], np.nan) # replace infinite returns with nan
	df.dropna(inplace = True)

	# feature set will be daily return for each ticker
	df_vals = df[[ticker for ticker in tickers]].pct_change()
	df_vals = df_vals.replace([np.inf, -np.inf], 0)
	df_vals.fillna(0, inplace = True)

	X = df_vals.values
	y = df['{}_target'.format(ticker)].values

	return X, y, df

def do_ml(ticker):
	X, y, df = extract_featureset(ticker)
	X_train, X_test, y_train, y_test = cross_validation.train_test_split(X, y, test_size = 0.25) #25% will be test set

	#clf = neighbors.KNeighborsClassifier()

	# ensemble of SVM, KNN, and Random Forest
	clf = VotingClassifier([('lsvc', svm.LinearSVC()),
							('knn', neighbors.KNeighborsClassifier()),
							('rfor', RandomForestClassifier())])
	clf.fit(X_train, y_train)
	confidence = clf.score(X_test, y_test)
	print('Accuracy:', confidence)
	predictions = clf.predict(X_test)
	print('Predicted spread:', Counter(predictions)) #distribution of predicted class

	return confidence


if __name__ == '__main__':
	main()

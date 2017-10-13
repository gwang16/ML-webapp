#import numpy as np
# for i in X_test:
# 	my_predictions.append(np.random.randint(0,2,1))
import random
from sklearn.metrics.pairwise import euclidean_distances
from scipy.spatial import distance

def euc(a, b):
	return distance.euclidean(a,b)

class ScrappyKNN():
	def fit(self, X_train, y_train):
		self.X_train = X_train
		self.y_train = y_train

	def predict(self, X_test):
		predictions = []
		for row in X_test:
			# random classifier
			# label = random.choice(self.y_train)
			label = self.closest(row)
			predictions.append(label)
		return predictions

	def closest(self, row):
		max_dist = euc(row, self.X_train[0])
		closest_label = 0
		for i in range(1, len(self.X_train)):
			dist = euc(row, self.X_train[i])
			if max_dist > dist:
				max_dist = dist
				closest_label = self.y_train[i]
				
		return closest_label


### model pipeline
# import a dataset
from sklearn import datasets
iris = datasets.load_iris()

X = iris.data
y = iris.target

# split into train and test
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = .5)

# classifier
# from sklearn.neighbors import KNeighborsClassifier
# my_classifier = KNeighborsClassifier()
my_classifier = ScrappyKNN()

# model fit / train classifier
my_classifier.fit(X_train, y_train)

# predict
predictions = my_classifier.predict(X_test)

# performance
from sklearn.metrics import accuracy_score
print(accuracy_score(y_test, predictions))
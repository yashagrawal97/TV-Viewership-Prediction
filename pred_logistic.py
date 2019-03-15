import numpy as np
import pandas as pd
import re

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
import pickle
import scipy.sparse as sp
from scipy.sparse import coo_matrix, hstack
import scipy

def import_tweets(filename, header = None):
    #import data from csv file via pandas library
    tweet_dataset = pd.read_csv(filename,header = header, encoding='Latin-1', low_memory=False, index_col=False)
    #the column names are based on sentiment140 dataset provided on kaggle
    tweet_dataset.columns = ['sentiment','id','date','flag','user','text']
    #delete 3 columns: flags,id,user, as they are not required for analysi
    for i in ['flag','id','user','date']: del tweet_dataset[i] # or tweet_dataset = tweet_dataset.drop(["id","user","date","user"], axis = 1)
    #in sentiment140 dataset, positive = 4, negative = 0; So we change positive to 1
    #tweet_dataset.sentiment = tweet_dataset.sentiment.replace(4,1)
    return tweet_dataset

def preprocess_tweet(tweet):
	#Preprocess the text in a single tweet
	#arguments: tweet = a single tweet in form of string
	#convert the tweet to lower case

	str(tweet)
	tweet.lower()
	#convert all urls to sting "URL "
	tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))','URL',tweet)
	#convert all @username to "AT_USER "
	tweet = re.sub('@[^\s]+','AT_USER', tweet)
	#correct all multiple white spaces to a single white space
	tweet = re.sub('[\s]+', ' ', tweet)
	#convert "#topic" to just "topic"
	tweet = re.sub(r'#([^\s]+)', r'\1', tweet)
	return tweet


def feature_extraction(data, method = "tfidf"):
	#arguments: data = all the tweets in the form of array, method = type of feature extracter
	#methods of feature extractions: "tfidf" and "doc2vec"
	if method == "tfidf":
		tfv=TfidfVectorizer(sublinear_tf=True, stop_words = "english") # we need to give proper stopwords list for better performance
		features=tfv.fit_transform(data)
	elif method == "doc2vec":
		None
	else:
		return "Incorrect inputs"
	return features

def train_classifier(features_train,features_test,label_train,label_test,classifier = "naive_bayes"):
    if classifier == "logistic_regression": # auc (train data): 0.8780618441250002
        model = LogisticRegression(C=1.)
    elif classifier == "naive_bayes": # auc (train data): 0.8767891829687501
        model = MultinomialNB()
    elif classifier == "svm": # can't use sklearn svm, as way too much of data so way to slow. have to use tensorflow for svm
        model = SVC()
    elif classifier == "random_forest":
        model = RandomForestClassifier(n_estimators=400, random_state=11)

    else:
        print("Incorrect selection of classifier")
	#fit model to data
    model.fit(features_train, label_train)
    print("Model fitting done...")
    accuracy=model.score(features_test,label_test)
    print("Accuracy is:")
    print(accuracy)
    #make prediction on the test data
    probability_to_be_positive = model.predict_proba(features_test)[:,1]
    #chcek AUC(Area Undet the Roc Curve) to see how well the score discriminates between negative and positive
    print ("auc (train data):" , roc_auc_score(label_test, probability_to_be_positive))
    #print top 10 scores as a sanity check
    print ("top 10 scores: ", probability_to_be_positive[:10])
    return model



#apply the preprocess function for all the tweets in the dataset
tweet_dataset = import_tweets("training_1600000_processed_noemoticon.csv")

#tweet_dataset = import_tweets("trainandtest.csv")
#tweet_dataset = import_tweets("new.csv")
print("File read")

tweet_dataset['text'] = tweet_dataset['text'].apply(preprocess_tweet)
print("Preprocessing done")

x = np.array(tweet_dataset.text)
y = np.array(tweet_dataset.sentiment)

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

data_train  = x_train
label_train = y_train
data_test   = x_test
label_test  = y_test

print("Extracting features")
tfv = TfidfVectorizer(sublinear_tf=True,stop_words="english")  # we need to give proper stopwords list for better performance
Tfidf_features_train=tfv.fit_transform(data_train)
Tfidf_features_test=tfv.transform(data_test)

bow_vectorizer = CountVectorizer(max_df=0.90, min_df=2, max_features=1000, stop_words='english') # bag-of-words feature matrix
bow_features_train = bow_vectorizer.fit_transform(data_train)
bow_features_test =  bow_vectorizer.transform(data_test)

features_final_train=hstack((Tfidf_features_train,bow_features_train))
features_final_test=hstack((Tfidf_features_test,bow_features_test))



print("Training")
model1=train_classifier(Tfidf_features_train,Tfidf_features_test, label_train,label_test, "naive_bayes")
model2=train_classifier(bow_features_train,bow_features_test, label_train,label_test, "naive_bayes")
model3=train_classifier(features_final_train,features_final_test, label_train,label_test, "naive_bayes")


prediction_dataset = pd.read_csv('tweet-2009.csv',usecols=range(12),encoding='Latin-1',index_col=False,low_memory=False)
prediction_dataset['Text'] = prediction_dataset['Text'].apply(preprocess_tweet)
x_prediction = np.array(prediction_dataset.Text)

features_x_prediction1=tfv.transform(x_prediction)
features_x_prediction2=bow_vectorizer.transform(x_prediction)
features_x_prediction=hstack((features_x_prediction1,features_x_prediction2))

prediction_dataset['Score_tfidf'] = model1.predict(features_x_prediction1)
prediction_dataset['Score_wordbag'] = model2.predict(features_x_prediction2)
prediction_dataset['Score_tfidf_wordbag'] = model3.predict(features_x_prediction)
prediction_dataset['Average_Score'] = 0.5*(prediction_dataset['Score_tfidf'] + prediction_dataset['Score_wordbag'] )


prediction_dataset.to_csv('output_pred.csv', index=False)



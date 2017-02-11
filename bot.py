#!/usr/bin/env python3.6
"""
The idea of this bot is to get a twitter stream to a select few
market influencing accounts wait for tweets, parse them for
tradable companies, sentiment analysis, create a trade within
some set risk limits and then execute the trade on Questrade platform.
"""
import csv
import os

import tweepy
from fuzzywuzzy import process

from nltk.sentiment.vader import SentimentIntensityAnalyzer  # need to nltk.download() the vader model

consumer_key = os.environ['TWITTER_CONSUMER_KEY']
consumer_secret = os.environ['TWITTER_CONSUMER_SECRET']
access_token = os.environ['TWITTER_ACCESS_TOKEN']
access_token_secret = os.environ['TWITTER_ACCESS_TOKEN_SECRET']

FOLLOWING = {
    '@POTUS': '822215679726100480',
    '@realDonaldTrump': '25073877',
    '@matt_warren': '14304643'
}

# constants for calculating position size
PORTFOLIO_SIZE = 1000
RISK_PERCENTAGE = 0.01
MAX_LEVERAGE = 5


def amount_to_trade(portfolio_size, risk, high, low, current, buy_or_sell):
    # this is not very sophisticated
    # strategy is to put a stop loss on the trade such that a bad call results in at most a loss of <risk>%
    if buy_or_sell == 'buy':
        stop = min([low, (current - (current * risk))])
        delta = current - stop
    else:
        # shorting
        stop = min([high, (current + (current * risk))])
        delta = stop - current

    position = (portfolio_size / risk) * delta
    return round(min(position, portfolio_size * MAX_LEVERAGE)), stop


class MyStreamListener(tweepy.StreamListener):

    def __init__(self):
        super().__init__()
        self.companies = {}
        self.ceos = {}
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        with open('sp500.csv') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                for company_name in row[1:]:
                    self.companies[company_name.strip()] = row[0]

        with open('ceos.csv') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.ceos[row[1]] = row[0]
                if row[0] in self.companies:
                    # treat mentions of the ceo as synonyms of the company
                    self.companies[row[1]] = self.companies[row[0]]

    def on_status(self, status):
        if status.user.id_str in FOLLOWING.values():
            matches = process.extract(status.text, self.companies.keys(), limit=1)
            if matches[0][1] > 80:
                print(f'I think this tweet is about {matches[0][0]} trading symbol: {self.companies[matches[0][0]]}')
            print(status.text)
            sentiment_scores = self.sentiment_analyzer.polarity_scores(status.text)
            print(sentiment_scores)
            for k in sorted(sentiment_scores):
                print('{0}: {1}, '.format(k, sentiment_scores[k]), end='')
            print()  # flush new line

    def on_error(self, status_code):
        if status_code == 403:
            print("The request is understood, but it has been refused or access is not allowed. Limit is maybe reached")
            return False


def test_parsing():
    company_names = {}
    with open('sp500.csv') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            for company_name in row[1:]:
                company_names[company_name.strip()] = row[0]
    matches = process.extract('Ford really killed it today', company_names.keys(), limit=1)
    assert(company_names[matches[0][0]] == 'F')
    matches = process.extract('testing a tweet about Ford', company_names.keys(), limit=3)
    assert(company_names[matches[0][0]] == 'F')
    print(matches)


def main():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.secure = True
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, retry_count=10, retry_delay=5, retry_errors=5)

    myStreamListener = MyStreamListener()
    myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
    myStream.filter(follow=FOLLOWING.values(), async=True)


if __name__ == '__main__':
    main()
    # test_parsing()

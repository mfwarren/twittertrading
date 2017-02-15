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
from yahoo_finance import Share
from nltk.sentiment.vader import SentimentIntensityAnalyzer  # need to nltk.download() the vader model

from questrade import Order, QuestradeClient

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
RISK_PERCENTAGE = 0.011
MAX_LEVERAGE = 5


def amount_to_trade(portfolio_size, risk, high, low, current, buy_or_sell):
    # this is not very sophisticated
    # strategy is to put a stop loss on the trade such that a bad call results in at most a loss of <risk>%
    if buy_or_sell == 'Buy':
        stop = min([low, (current - (current * risk))])
        delta = current - stop
        buysell = 'Buy'
    else:
        # shorting
        stop = min([high, (current + (current * risk))])
        delta = stop - current
        buysell = 'Short'

    position = (portfolio_size / risk) * delta
    return round(min(position, portfolio_size * MAX_LEVERAGE) / current), stop, buysell


class MyStreamListener(tweepy.StreamListener):

    def __init__(self):
        super().__init__()
        self.companies = {}
        self.ceos = {}
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.questrade_client = QuestradeClient()

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

    def process_tweet(self, text):
        matches = process.extract(text, self.companies.keys(), limit=1)
        print(text)
        print(matches)
        if matches[0][1] > 90:
            print(f'I think this tweet is about {matches[0][0]} trading symbol: {self.companies[matches[0][0]]}')
        else:
            print('unable to match a company in this tweet')
            return
        print(text)
        sentiment_scores = self.sentiment_analyzer.polarity_scores(text)
        print(sentiment_scores)
        for k in sorted(sentiment_scores):
            print('{0}: {1}, '.format(k, sentiment_scores[k]), end='')
        print()  # flush new line

        # lookup current price, daily high and low
        stock = Share(self.companies[matches[0][0]])
        price = float(stock.get_price())
        high = float(stock.get_days_high())
        low = float(stock.get_days_low())

        if sentiment_scores['neg'] > 0.75:
            # negative sentiment on the stock, short it
            position = amount_to_trade(PORTFOLIO_SIZE, RISK_PERCENTAGE, high, low, price, 'Short')

        elif sentiment_scores['pos'] > 0.5:
            # positive or neutral sentiment on the stock, buy it
            position = amount_to_trade(PORTFOLIO_SIZE, RISK_PERCENTAGE, high, low, price, 'Buy')

        else:
            position = (0, 0, 'No Order')

        print(f'Execute Trade: {position[2]} {position[0]} of {self.companies[matches[0][0]]}, set stop loss at {position[1]}')

        questrade_symbol = self.questrade_client.get_symbol(self.companies[matches[0][0]])
        print(questrade_symbol)
        if questrade_symbol:
            order = Order(os.getenv('QUESTRADE_ACCOUNT_NUMBER'),
                        questrade_symbol['symbolId'],
                        position[0],
                        None,
                        stop_price=position[1],
                        action=position[2])
            trade = self.questrade_client.create_order(order)
            print(trade)

    def on_status(self, status):
        if status.user.id_str in FOLLOWING.values():
            self.process_tweet(status.text)

    def on_error(self, status_code):
        if status_code == 403:
            print("The request is understood, but it has been refused or access is not allowed. Limit is maybe reached")
            return False


def main():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.secure = True
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, retry_count=10, retry_delay=5, retry_errors=5)

    myStreamListener = MyStreamListener()
    myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)
    myStream.filter(follow=FOLLOWING.values(), async=True)

    myStreamListener.process_tweet('Remarks by President Trump at Swearing-In Ceremony for Treasury Secretary Mnuchin')
    myStreamListener.process_tweet('Remarks by President Trump at Parent-Teacher Conference Listening Session ')
    myStreamListener.process_tweet('Watch Dr. David Shulkin- new @DeptVetAffairs Secretary being sworn-in by @VP Pence https://t.co/fjJOpFkqi5 https://t.co/s9ZGynLM2i')


if __name__ == '__main__':
    main()

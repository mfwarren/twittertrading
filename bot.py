#!/usr/bin/env python3.6
"""
The idea of this bot is to get a twitter stream to a select few
market influencing accounts wait for tweets, parse them for
tradable companies, sentiment analysis, create a trade within
some set risk limits and then execute the trade on Questrade platform.
"""
import os

import tweepy


FOLLOWING = {
    '@POTUS': 822215679726100480,
    '@realDonaldTrump': 25073877
}


class MyStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        print(status.text)

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener())
myStream.filter(follow='POTUS')
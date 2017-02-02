#!/usr/bin/env python3.6
"""
The idea of this bot is to get a twitter stream to a select few
market influencing accounts wait for tweets, parse them for
tradable companies, sentiment analysis, create a trade within
some set risk limits and then execute the trade on Questrade platform.
"""
import os

import tweepy

consumer_key = os.environ['TWITTER_CONSUMER_KEY']
consumer_secret = os.environ['TWITTER_CONSUMER_SECRET']
access_token = os.environ['TWITTER_ACCESS_TOKEN']
access_token_secret = os.environ['TWITTER_ACCESS_TOKEN_SECRET']

FOLLOWING = {
    '@POTUS': '822215679726100480',
    '@realDonaldTrump': '25073877',
    '@matt_warren': '14304643'
}



class MyStreamListener(tweepy.StreamListener):

    def on_status(self, status):
        if status.user.id_str in FOLLOWING.values():
            print(status.text)

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


if __name__ == '__main__':
    main()
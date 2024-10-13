import praw
from dotenv import load_dotenv
import os
import datetime
import re

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_API_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_API_CLIENT_SECRET'),
    user_agent="USERAGENT"
)

EXCLUDE_WORD_LIST = ['DIP','SPY','JPY','WWE','UFC','USD']

def get_posts_from_subreddit_today(subreddit):
    return reddit.subreddit(subreddit).search(query='*', sort='new', time_filter='week')

def filter_tickers_from_posts_for_today(posts, flair_list):
    tickers = []
    midnight = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    utc_midnight_today = midnight.replace(tzinfo=datetime.timezone.utc).timestamp()
    for post in posts:
        if post.created_utc >= utc_midnight_today:
            if (post.link_flair_text in flair_list):
                tickers = tickers + filter_ticker_from_post_title(post.title)
    return tickers

def filter_ticker_from_post_title(post_title):
    all_caps_words = get_all_caps_words(post_title)
    all_caps_words_with_exclusion = list(set(all_caps_words) - set(EXCLUDE_WORD_LIST))
    return all_caps_words_with_exclusion


def get_all_caps_words(text):
  #remove words with 2 letters or less then
  #returns a list of all words in the text that are in all caps
  text = re.sub(r'\b\w{1,2}\b', '', text)
  pattern = re.compile(r"\b[A-Z]+\b")
  return pattern.findall(text)



    

import praw
from dotenv import load_dotenv
import os
import datetime
import re
import requests

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_API_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_API_CLIENT_SECRET'),
    user_agent="USERAGENT"
)

EXCLUDE_WORD_LIST = ['DIP','SPY','JPY','WWE','UFC','USD']

def get_posts_from_subreddit_in_one_week(subreddit):
    return reddit.subreddit(subreddit).search(query='*', sort='new', time_filter='week')

def get_top_level_comments(post):
    """
    Fetch all top-level comments from a given Reddit post.
        
    :param post: A PRAW submission object
    :return: A list of top-level comments
    """
    post.comments.replace_more(limit=None)
    return post.comments.list()
    """
    Fetch all comments from a given Reddit post.
    
    :param post: A PRAW submission object
    :param expand_level: The level of 'more comments' to expand (default 0 for first level comments only)
    :return: A list of all comments
    """
    def fetch_all_comments_recursive(comment, level=0, max_level=None):
        if max_level is not None and level > max_level:
            return []
        
        comments = [comment]
        if hasattr(comment, 'replies'):
            comment.replies.replace_more(limit=None)
            for reply in comment.replies:
                comments.extend(fetch_all_comments_recursive(reply, level + 1, max_level))
        return comments

    all_comments = []
    post.comments.replace_more(limit=None)
    for top_level_comment in post.comments:
        all_comments.extend(fetch_all_comments_recursive(top_level_comment, max_level=expand_level))
    return all_comments
 

def download_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f"Image downloaded successfully: {save_path}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")

        
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



# Create a RedditParser class to encapsulate the functionality
class RedditParser:
    @staticmethod
    def get_posts_from_subreddit_in_one_week(subreddit):
        return get_posts_from_subreddit_in_one_week(subreddit)
    
    @staticmethod
    def filter_tickers_from_posts_for_today(posts, flair_list):
        return filter_tickers_from_posts_for_today(posts, flair_list)
    
    @staticmethod
    def filter_ticker_from_post_title(post_title):
        return filter_ticker_from_post_title(post_title)
    
    @staticmethod
    def get_all_caps_words(text):
        return get_all_caps_words(text)
    
    @staticmethod
    def get_posts_with_flair(subreddit, flair_text):
        """
        Fetch all posts with a specific flair from a subreddit.
        
        :param subreddit: The name of the subreddit
        :param flair_text: The text of the flair to filter posts by
        :return: A list of posts with the specified flair
        """
        query = f'flair:"{flair_text}"'
        posts = reddit.subreddit(subreddit).search(query, sort='new')
        return list(posts)

    @staticmethod
    def get_top_posts(subreddit, limit=10):
        """
        Fetch the top posts from a subreddit.
        
        :param subreddit: The name of the subreddit
        :param limit: The number of top posts to retrieve (default is 10)
        :return: A list of top posts
        """
        return list(reddit.subreddit(subreddit).top(limit=limit))
        return fetch_all_comments(post)

    @staticmethod
    def download_image(url, save_path):
        return download_image(url, save_path)

# Optionally, you can also export the individual functions
__all__ = ['RedditParser', 'get_posts_from_subreddit_in_one_week', 'filter_tickers_from_posts_for_today', 
           'filter_ticker_from_post_title', 'get_all_caps_words']

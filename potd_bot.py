import datetime
from bots.nfl_bot import RedditParser

def get_potd_posts(reddit_parser, subreddit="sportsbook"):
    """
    Fetch and filter posts with the flair 'POTD' from the specified subreddit.
    
    :param reddit_parser: An instance of RedditParser
    :param subreddit: The subreddit to search in (default is "sportsbook")
    :return: A list of posts with the flair 'POTD'
    """
    # Get today's and yesterday's date in the format "MM/DD" or "M/D"
    today = datetime.datetime.now().strftime("%-m/%-d")
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%-m/%-d")
    
    # Fetch all posts with the flair 'POTD'
    potd_posts = reddit_parser.get_posts_with_flair(subreddit, "POTD")
    
    # Filter posts created today
    today_posts = [post for post in potd_posts if datetime.datetime.fromtimestamp(post.created_utc).strftime("%-m/%-d") == today]
    
    if today_posts:
        return today_posts
    else:
        # If no posts today, find the latest post from yesterday
        yesterday_posts = [post for post in potd_posts if datetime.datetime.fromtimestamp(post.created_utc).strftime("%-m/%-d") == yesterday]
        if yesterday_posts:
            return [max(yesterday_posts, key=lambda post: post.created_utc)]  # Return the latest single post from yesterday
        return []  # Return an empty list if no posts are found

def main():
    # Initialize RedditParser
    reddit_parser = RedditParser()
    potd_posts = get_potd_posts(reddit_parser)
    print(f"\nFound {len(potd_posts)} POTD posts today:")
    for post in potd_posts:
        print(f"Title: {post.title}")
        print(f"URL: {post.url}")
        print("---")

if __name__ == "__main__":
    main()

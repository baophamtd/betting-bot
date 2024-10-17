import sys
import os
import datetime 

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from helpers.tools.reddit_parser import RedditParser

def get_nfl_player_prop_posts(reddit_parser, subreddit="sportsbook"):
    """
    Fetch and filter posts containing NFL Player props from the specified subreddit.
    
    :param reddit_parser: An instance of RedditParser
    :param subreddit: The subreddit to search in (default is "sportsbook")
    :return: A list of posts containing NFL Player props
    """
    # Fetch all posts from today
    all_posts = reddit_parser.get_posts_from_subreddit_today(subreddit)
    
    # Filter posts containing NFL Player props
    nfl_player_prop_posts = []
    for post in all_posts:
        title_lower = post.title.lower()
        if "nfl" in title_lower and "player prop" in title_lower:
            nfl_player_prop_posts.append(post)
    
    return nfl_player_prop_posts

def iterate_comments(reddit_parser, post):
    """
    Fetch and iterate through all comments of a given post, printing each comment.
    
    :param reddit_parser: An instance of RedditParser
    :param post: A PRAW submission object
    """
    comments = reddit_parser.fetch_all_comments(post)
    
    print(f"\nComments for post: {post.title}")
    print("-" * 50)
    
    for i, comment in enumerate(comments, 1):
        print(f"Comment {i}:")
        print(comment.body)
        print("-" * 30)


# Example usage in main function:
def main():
    # Initialize RedditParser
    reddit_parser = RedditParser()

    # Get NFL Player prop posts
    nfl_prop_posts = get_nfl_player_prop_posts(reddit_parser)
    print(f"\nFound {len(nfl_prop_posts)} NFL Player prop posts:")
    for post in nfl_prop_posts:
        print(f"Title: {post.title}")
        print(f"URL: {post.url}")
        print("---")
    # Get today's date in the format "MM/DD" or "M/D"
    today = datetime.datetime.now().strftime("%-m/%-d")

    # Iterate through NFL prop posts
    for post in nfl_prop_posts:
        title_lower = post.title.lower()
        
        # Check if the post title contains today's date
        if today.lower() in title_lower:
            print(f"\nProcessing post: {post.title}")
            print(f"URL: {post.url}")
            print("Comments:")
            
            # Fetch and iterate through comments
            comments = reddit_parser.fetch_all_comments(post)
            for comment in comments:
                print("-" * 40)
                print(comment.body)
            
            print("\n" + "=" * 50 + "\n")  # Separator between posts

if __name__ == "__main__":
    main()







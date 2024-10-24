import sys
import os
import datetime 
import re 
import requests
from PIL import Image
from io import BytesIO
import pytesseract

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from helpers.tools.reddit_parser import RedditParser
from helpers.tools.odds_api import OddsAPI 
from helpers.tools.ocr_api import OCRAPI  # Add this import

# Add this constant near the top of your file, after imports
BOT_USERNAME = 'sbpotdbot'

def get_nfl_player_prop_posts(reddit_parser, subreddit="sportsbook"):
    """
    Fetch and filter posts containing NFL Player props from the specified subreddit.
    
    :param reddit_parser: An instance of RedditParser
    :param subreddit: The subreddit to search in (default is "sportsbook")
    :return: A list of posts containing NFL Player props
    """
    # Fetch all posts from today

    all_posts = reddit_parser.get_posts_from_subreddit_in_one_week(subreddit)
    
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

    # Create a file on the Desktop to store all comments
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    comments_file_path = os.path.join(desktop_path, "reddit_comments.txt")

    # Open the file in write mode
    with open(comments_file_path, "w", encoding="utf-8") as comments_file:
        # Write each comment to the file
        for comment in comments:
            # Skip comments by the bot
            if comment.author and comment.author.name.lower() == BOT_USERNAME.lower():
                continue
            # Check if the comment body contains a URL matching the specified format
            url_pattern = r'https://preview\.redd\.it/[a-zA-Z0-9]+\.(png|jpg|jpeg|gif)\?.*'
            match = re.search(url_pattern, comment.body)
            if match:
                image_url = match.group(0)
                # Generate a unique filename using the comment's ID
                filename = f"reddit_image_{comment.id}.{match.group(1)}"
                save_path = os.path.join(desktop_path, filename)
                # Download the image
                reddit_parser.download_image(image_url, save_path)

                # Initialize the OCRAPI
                ocr_api = OCRAPI()

                # Perform OCR on the downloaded image using the OCRAPI
                extracted_text = ocr_api.image_to_text(save_path)
                print(f"OCR result for {filename}:")
                print(extracted_text)
                print("-" * 50)
                # Remove the image URL from the comment body
                comments_file.write(f"Image saved: {filename}\n")
                comment.body = re.sub(url_pattern, extracted_text, comment.body).strip()
            comments_file.write(f"Author: {comment.author}\n")
            comments_file.write(f"Created UTC: {datetime.datetime.fromtimestamp(comment.created_utc)}\n")
            comments_file.write(f"Body:\n{comment.body}\n")
            comments_file.write("-" * 50 + "\n\n")

    print(f"Comments have been saved to: {comments_file_path}")
    return comments

# Example usage:
# image_url = "https://example.com/path/to/image.jpg"
# extracted_text = convert_image_url_to_text(image_url)
# print(extracted_text)



# Example usage in main function:
def main():
    # Initialize RedditParser
    reddit_parser = RedditParser()
    # Initialize OddsAPI
    odds_api = OddsAPI()

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
        # Get the most recent date from the post titles
        most_recent_date = None
        for p in nfl_prop_posts:
            date_match = re.search(r'(\d{1,2}/\d{1,2})', p.title)
            if date_match:
                post_date = datetime.datetime.strptime(date_match.group(1), "%m/%d").replace(year=datetime.datetime.now().year)
                if most_recent_date is None or post_date > most_recent_date:
                    most_recent_date = post_date

        # Convert most_recent_date to string format
        most_recent_date_str = most_recent_date.strftime("%-m/%-d") if most_recent_date else None
        most_recent_date_str = "10/21"
        print(f"Most recent date: {most_recent_date_str}")
        # Check if the post title contains today's date or the most recent date
        if most_recent_date_str and most_recent_date_str.lower() in title_lower:
            print(f"\nProcessing post: {post.title}")
            print(f"URL: {post.url}")
            # Update this line:
            iterate_comments(reddit_parser, post)  # Pass both reddit_parser and post

            print("-" * 40)

            print("\n" + "=" * 50 + "\n")  # Separator after all comments
            """
            def get_all_nfl_bovada_odds(odds_api):
                odds_map = {}
                try:
                    nfl_odds = odds_api.get_nfl_odds_bovada()
                    print(f"Number of games returned: {len(nfl_odds)}")
                    for game in nfl_odds:
                        home_team = game['home_team']
                        away_team = game['away_team']
                        match_name = f"{away_team} @ {home_team}"
                        # Fetch player props for each game
                        print(f"Fetching player props for {match_name}...")
                        try:
                            # Define all NFL player prop market keys
                            nfl_markets = (
                                "player_pass_tds,player_pass_yds,player_pass_completions,"
                                "player_pass_attempts,player_rush_yds,player_rush_reception_yds,"
                                "player_rush_attempts,player_receptions,player_reception_yds,player_rush_longest"
                            )
                            player_props = odds_api.get_player_props(game['id'], nfl_markets)
                            if player_props:
                                for prop in player_props:
                                    for outcome in prop['outcomes']:
                                        description = outcome.get('description', prop['key'])
                                        name = outcome['name']
                                        point = outcome.get('point', '')
                                        key = f"{description} {name} {point}"
                                        odds_map[key] = {
                                            'match': match_name,
                                            'price': outcome['price']
                                        }
                            else:
                                print(f"No player props available for {match_name}.")
                        except Exception as e:
                            print(f"Error fetching player props for {match_name}: {str(e)}")
                except Exception as e:
                    print(f"Error fetching NFL odds: {str(e)}")
                
                return odds_map

            # Call the function and store the result
            all_nfl_odds = get_all_nfl_bovada_odds(odds_api)
            print("All NFL Bovada odds:")
            for key, value in all_nfl_odds.items():
                print(f"{key}: {value}")


            print("\n" + "=" * 50 + "\n")  # Separator after odds
            """


if __name__ == "__main__":
    main()







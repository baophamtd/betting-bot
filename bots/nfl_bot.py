import sys
import os
import datetime 
import re 

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from helpers.tools.reddit_parser import RedditParser
from helpers.tools.odds_api import OddsAPI 
from helpers.tools.ocr_api import OCRAPI  # Add this import
#from helpers.tools.langchain_client import LangChainClient

# Username of the bot, used to filter out its own comments
BOT_USERNAME = 'sbpotdbot'
# Path to the folder where all comments will be saved
ANALYZING_RESULT_FOLDER = os.path.join(project_root, "bots", "analyzing_results")


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
    Fetch and iterate through all comments of a given post, saving them in batches of 100.
    
    :param reddit_parser: An instance of RedditParser
    :param post: A PRAW submission object
    """
    comments = reddit_parser.fetch_all_comments(post)
    
    print(f"\nProcessing comments for post: {post.title}")

    # Extract date from post title
    date_match = re.search(r'(\d{1,2}/\d{1,2})', post.title)
    if date_match:
        current_date = datetime.datetime.strptime(date_match.group(1), "%m/%d").strftime("%m-%d")
    else:
        current_date = datetime.datetime.now().strftime("%m-%d")
        print(f"Warning: Could not extract date from post title. Using current date: {current_date}")

    file_counter = 1
    comment_counter = 0
    
    # Ensure the ANALYZING_RESULT_FOLDER exists
    os.makedirs(ANALYZING_RESULT_FOLDER, exist_ok=True)

    def write_comment_to_file(file, comment):
        file.write(f"Author: {comment.author}\n")
        file.write(f"Created UTC: {datetime.datetime.fromtimestamp(comment.created_utc)}\n")
        file.write(f"Body:\n{comment.body}\n")
        file.write("-" * 50 + "\n\n")

    current_file = None
    for comment in comments:
        # Skip comments by the bot
        if comment.author and comment.author.name.lower() == BOT_USERNAME.lower():
            continue

        # Start a new file if we've reached 100 comments or it's the first comment
        if comment_counter % 100 == 0:
            if current_file:
                current_file.close()
            filename = f"reddit_comments_{current_date}_{file_counter}.txt"
            file_path = os.path.join(ANALYZING_RESULT_FOLDER, filename)
            current_file = open(file_path, "w", encoding="utf-8")
            file_counter += 1

        # Check if the comment body contains a URL matching the specified format
        url_pattern = r'https://preview\.redd\.it/[a-zA-Z0-9]+\.(png|jpg|jpeg|gif)\?.*'
        match = re.search(url_pattern, comment.body)
        if match:
            image_url = match.group(0)
            # Generate a unique filename using the comment's ID
            image_filename = f"reddit_image_{comment.id}.{match.group(1)}"
            save_path = os.path.join(ANALYZING_RESULT_FOLDER, image_filename)
            # Download the image
            reddit_parser.download_image(image_url, save_path)

            # Initialize the OCRAPI
            ocr_api = OCRAPI()

            # Perform OCR on the downloaded image using the OCRAPI
            extracted_text = ocr_api.image_to_text(save_path)
            print(f"OCR result for {image_filename}:")
            print(extracted_text)
            print("-" * 50)
            # Remove the image URL from the comment body
            print(f"Image processed: {image_filename}\n")
            comment.body = re.sub(url_pattern, extracted_text, comment.body).strip()

            # Delete the image file after OCR
            try:
                os.remove(save_path)
                print(f"Deleted image file: {save_path}")
            except OSError as e:
                print(f"Error deleting image file {save_path}: {e}")

        write_comment_to_file(current_file, comment)
        comment_counter += 1

    # Close the last file if it's still open
    if current_file:
        current_file.close()

    print(f"Processed {comment_counter} comments.")
    print(f"Comments have been saved to {file_counter - 1} files in: {ANALYZING_RESULT_FOLDER}")
    return comments

def get_all_nfl_bovada_odds(odds_api):
    odds_map = {}
    current_date = datetime.datetime.now().strftime("%m-%d")
    odds_file_path = os.path.join(ANALYZING_RESULT_FOLDER, f"bovada_odds_{current_date}.txt")

    # Ensure the ANALYZING_RESULT_FOLDER exists
    os.makedirs(ANALYZING_RESULT_FOLDER, exist_ok=True)

    def convert_prop_name(key):
        prop_name_map = {
            'player_pass_tds': 'Passing Touchdowns',
            'player_pass_yds': 'Passing Yards',
            'player_pass_completions': 'Pass Completions',
            'player_pass_attempts': 'Pass Attempts',
            'player_rush_yds': 'Rushing Yards',
            'player_rush_reception_yds': 'Rush + Reception Yards',
            'player_rush_attempts': 'Rushing Attempts',
            'player_receptions': 'Receptions',
            'player_reception_yds': 'Receiving Yards',
            'player_rush_longest': 'Longest Rush',
            'player_pass_interceptions': 'Pass Interceptions',
            'player_sacks': 'Sacks',
            'player_anytime_td': 'Player Anytime Touchdown'
        }
        return prop_name_map.get(key, key.replace('_', ' ').title())

    with open(odds_file_path, 'w', encoding='utf-8') as odds_file:
        try:
            nfl_odds = odds_api.get_nfl_odds_bovada()
            print(f"Number of games returned: {len(nfl_odds)}")

            for game in nfl_odds:
                home_team = game['home_team']
                away_team = game['away_team']
                # Extract and convert commence_time to EST
                commence_time_utc = game['commence_time']  # Assuming this is in ISO format
                commence_time = datetime.datetime.fromisoformat(commence_time_utc[:-1])  # Remove 'Z' for conversion
                commence_time_est = commence_time - datetime.timedelta(hours=5)  # Convert to EST (UTC-5)
                match_name = f"{away_team} @ {home_team} | Start Time: {commence_time_est.strftime('%Y-%m-%d %H:%M:%S')} EST"
                print(f"Fetching player props for {match_name}...")

                try:
                    # Define all NFL player prop market keys
                    nfl_markets = (
                        "player_pass_tds,player_pass_yds,player_pass_completions,player_pass_longest_completion,"
                        "player_pass_attempts,player_rush_yds,player_rush_reception_yds,"
                        "player_rush_attempts,player_receptions,player_reception_yds,player_rush_longest,player_reception_longest,"
                        "player_pass_interceptions,player_sacks,player_anytime_td"
                    )
                    player_props = odds_api.get_player_props(game['id'], nfl_markets)
                    if player_props:
                        for prop in player_props:
                            prop_name = convert_prop_name(prop['key'])
                            for outcome in prop['outcomes']:
                                description = outcome.get('description', '')
                                name = outcome['name']
                                point = outcome.get('point', '')
                                over_under = ""
                                if name.lower() in ['over', 'under']:
                                    over_under = f"{name} {point} "
                                key = f"{description} - {over_under}{prop_name}"
                                price = outcome['price']
                                odds_map[key] = {
                                    'match': match_name,
                                    'price': price
                                }
                                # Write the odds line to the file
                                odds_line = f"{match_name} | {key} | Price: {price}\n"
                                odds_file.write(odds_line)
                    else:
                        print(f"No player props available for {match_name}.")
                except Exception as e:
                    error_message = f"Error fetching player props for {match_name}: {str(e)}"
                    print(error_message)
                    odds_file.write(f"{error_message}\n")
                
                odds_file.write("\n")  # Add a blank line between games
        except Exception as e:
            error_message = f"Error fetching NFL odds: {str(e)}"
            print(error_message)
            odds_file.write(f"{error_message}\n")

    print(f"Odds have been saved to: {odds_file_path}")
    return odds_map


# Example usage in main function:
def main():
    # Initialize RedditParser
    reddit_parser = RedditParser()
    # Initialize OddsAPI
    odds_api = OddsAPI()
    # Initialize LangChainClient
    #langchain_client = LangChainClient(model_name="gpt-3.5-turbo")

    # Get NFL Player prop posts
    nfl_prop_posts = get_nfl_player_prop_posts(reddit_parser)
    print(f"\nFound {len(nfl_prop_posts)} NFL Player prop posts:")
    post = None
    for post in nfl_prop_posts:
        print(f"Title: {post.title}")
        print(f"URL: {post.url}")
        print("---")
    # Get today's date in the format "MM/DD" or "M/D"
    today = datetime.datetime.now().strftime("%-m/%-d")

    # Find the most recent date before the main loop
    most_recent_date = None
    for p in nfl_prop_posts:
        date_match = re.search(r'(\d{1,2}/\d{1,2})', p.title)
        if date_match:
            post_date = datetime.datetime.strptime(date_match.group(1), "%m/%d").replace(year=datetime.datetime.now().year)
            if most_recent_date is None or post_date > most_recent_date:
                most_recent_date = post_date

    most_recent_date_str = most_recent_date.strftime("%-m/%-d") if most_recent_date else None
    #most_recent_date_str = "10/21"  # Note: This line overwrites the actual most recent date
    print(f"Most recent date: {most_recent_date_str}")

    # Get all NFL Bovada odds
    print("\nFetching all NFL Bovada odds...")
    odds_map = get_all_nfl_bovada_odds(odds_api)
    print("Finished fetching NFL Bovada odds.")

    # Iterate through NFL prop posts
    for post in nfl_prop_posts:
        title_lower = post.title.lower()
        
        # Check if the post title contains the most recent date
        if most_recent_date_str and most_recent_date_str.lower() in title_lower:
            print(f"\nProcessing post: {post.title}")
            print(f"URL: {post.url}")
            iterate_comments(reddit_parser, post)
            print("-" * 40)
            print("\n" + "=" * 50 + "\n")  # Separator after all comments


if __name__ == "__main__":
    main()









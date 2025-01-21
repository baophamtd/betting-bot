from contextlib import ExitStack
import sys
import os
import datetime 
import re 
import emoji
import pytz


# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from helpers.tools.reddit_parser import RedditParser
from helpers.tools.telegram_bot_client import TelegramBotClient 
from helpers.tools.openai_client import OpenAIClient 


# Username of the bot, used to filter out its own comments
BOT_USERNAME = 'sbpotdbot'
# Path to the folder where all comments will be saved
POTD_DATA_FOLDER = os.path.join(project_root, "bots", "potd_data")

def get_potd_posts(reddit_parser, subreddit="sportsbook"):
    """
    Fetch and filter posts containing POTD from the specified subreddit.

    :param reddit_parser: An instance of RedditParser
    :param subreddit: The subreddit to search in (default is "sportsbook")
    :return: A list of posts containing POTD
    """
    # Fetch all posts with the flair "POTD" from the subreddit
    potd_posts = reddit_parser.get_posts_with_flair(subreddit, "POTD")
   
    # Get today's and tomorrow's date in PST
    pst = pytz.timezone('America/Los_Angeles')
    today = datetime.datetime.now(pst).strftime("%-m/%-d/%y")
    tomorrow = (datetime.datetime.now(pst) + datetime.timedelta(days=1)).strftime("%-m/%-d/%y")
     
    print(f"Today's date (PST): {today}")
    print(f"Tomorrow's date (PST): {tomorrow}")
    print(f"potd_posts: {len(potd_posts)}")
    
    # Filter posts for tomorrow's date
    tomorrow_posts = [post for post in potd_posts if extract_date_from_title(post.title) == tomorrow]
  
    if tomorrow_posts:
        return tomorrow_posts[:1]  # Return the latest single post for tomorrow
    
    # If no posts for tomorrow, filter posts for today's date
    today_posts = [post for post in potd_posts if extract_date_from_title(post.title) == today]
  
    if today_posts:
        return today_posts[:1]  # Return the latest single post for today
    
    return []  # Return an empty list if no posts for today or tomorrow
 
def extract_date_from_title(title):
    """
    Extract the date from the post title in the format MM/DD/YY.

    :param title: The title of the post
    :return: The extracted date as a string in the format MM/DD/YY, or None if no date is found
    """
    match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{2})\b', title)
    return match.group(1) if match else None


    
def save_comments_to_file(comments, file_name):
    """
    Save the comments of a post to a file.

    :param comments: A list of comments to save
    :param file_name: The name of the file to save the comments in
    """
    # Create a folder for the post's comments
    post_folder = os.path.join(POTD_DATA_FOLDER)
    os.makedirs(post_folder, exist_ok=True)

    # Save all comments to the file
    file_path = os.path.join(post_folder, file_name)
    with open(file_path, "w") as file:
        for comment in comments:
            # Skip comments by the bot
            if comment.author and comment.author.name.lower() == BOT_USERNAME.lower():
                continue
            
            author = comment.author.name if comment.author else 'Unknown'
            created_time = datetime.datetime.fromtimestamp(comment.created_utc).strftime("%Y-%m-%d %H:%M:%S")
            comment_body = convert_emojis_to_text(comment.body)
            comment_body = "\n".join([line for line in comment_body.splitlines() if line.strip() != ""])
            file.write(f"Author: {author}\n")
            file.write(f"Created UTC: {created_time}\n")
            file.write(f"{comment_body}\n")
            file.write("\n" + "=" * 90 + "\n\n")

def convert_emojis_to_text(comment):
    """
    Convert any emoji detected in a string comment to the closest text possible.

    :param comment: The comment string containing emojis
    :return: The comment string with emojis converted to text
    """
    return emoji.demojize(comment)
 
def create_potd_assistant(openai_client):
     # Create an assistant                         
     assistant = openai_client.create_assistant(   
         assistant_name="potd_assistant",          
         instructions="""
     # CONTEXT #
     You are a sports betting advisor that has the latest information of all teams and players from all sports.
     I'm going to provide you a list of suggestions for Pick of The Day (POTD) from different sport betting advisors.
     In each of the suggestion, the author will provide their track record of their recent predictions (if available), and the reason why they think their bet is a good bet for today.
     Each suggestion is separated by a line break made up of 90 equal signs.
     This is an example of their suggestion:
     
     Author: test_author
     Created UTC: 2025-01-17 17:17:14
     Record: 20-4 (4 pushes) 
     Net Units: +22.83E
     ROI: +38%
     Sport: Champion League Soccer
     Pick: Hannover U23 – Erzgebirge Aue / Over 2.5
     Write Up: This pick is from my soccer model that I've been using for the past two years. It assigns ELO ratings to players and projects a win chance based on the combined ELO ratings of the players on each team. TeamReddit is projecting a 62% win chance here which creates value here on the ML.

     Note: The example above is just a template. The actual suggestions will vary in format and content.
     
     # OBJECTIVE #
     You need to go through all of the suggestions. Look at each other track record. Then look at the reason of their bet. Then use your knowledge from the latest information about the teams/players in the match and tell me what is the best bet for today.
     Remember, you have to incorporate your knowledge obtained from the internet too.
     Try to give me only one single best bet, but if you think there are a few bets that rank equal in terms of quality then give me all of them.
     
     # STYLE #
     A check mark or anything that has the same meaning usually means that it is a win.
     A cross mark or anything that has the same meaning usually means that it is a loss.
     
     # TONE #
     Brief
     
     # RESPONSE #
     Each response you need to tell me exactly what to bet on and which author the bet come from.
     Then why you agree with the author and give their track record.
     If there are multiple bets, then bullet point them."""
     )
     return assistant
                                                                                                                              

# Example usage in main function:
def main():
    # Initialize RedditParser                                                                                                
    reddit_parser = RedditParser()                                                                                           
    # Initialize OpenAIClient                     
    openai_client = OpenAIClient()    
    # Initialize TelegramBotClient
    telegram_bot_client = TelegramBotClient()            
                
    potd_posts = get_potd_posts(reddit_parser)                                                                               
    print(f"\nFound {len(potd_posts)} POTD posts today:")   
    # get first post
    latest_post = potd_posts[0]                                                                 
    print(f"Title: {latest_post.title}")                                                                              
    comments = reddit_parser.fetch_all_comments(latest_post)
    # Generate the file name from the post title
    file_name = latest_post.title.replace(" ", "-").replace("/", "-") + ".txt"
    save_comments_to_file(comments, file_name)   
                                
    # Create an assistant                         
    assistant = create_potd_assistant(openai_client)   
    # Get all file paths under POTD_DATA_FOLDER
    file_paths = [os.path.join(POTD_DATA_FOLDER, file) for file in os.listdir(POTD_DATA_FOLDER) if os.path.isfile(os.path.join(POTD_DATA_FOLDER, file))]
    # Create Vector Store
    openai_client.create_vector_store_for_assistant_with_file_paths(assistant.id, "potd_vector_store", file_paths)

    # Ask the important question to the assistant
    query = "What are the best bet(s) for tomorrow?"
    
    response = openai_client.query_assistant(assistant.id, query)
    print(f"Assistant Response: {response}")
    
    openai_client.delete_all_vector_stores()
    
    # Remove all files in POTD_DATA_FOLDER
    for file in file_paths:
        os.remove(file)
    print("All files in POTD_DATA_FOLDER have been removed.")

     
    telegram_bot_client.send_message(f"POTD Assistant: {response}")
    
if __name__ == "__main__":
    main()
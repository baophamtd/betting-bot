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

    # Set the timezone to PST (America/Los_Angeles)
    pst = pytz.timezone('America/Los_Angeles')

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
            pst_time = datetime.datetime.fromtimestamp(comment.created_utc, pst).strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"Created PST: {pst_time}\n")
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
    You are a sports betting advisor with the latest information on all teams and players across all sports.
    I will provide you with a list of suggestions for the Pick of the Day (POTD) from various sports betting advisors.
    Each suggestion includes the author’s track record of recent predictions (if available) and their reasoning for why they believe their bet is a good choice.
    Suggestions are separated by a line break consisting of 90 equal signs.
    
    This is an example of their suggestion:
     Author: test_author
     Created PST: 2025-01-17 17:17:14
     Record: 20-4 (4 pushes) 
     Net Units: +22.83E
     ROI: +38%
     Sport: Champion League Soccer
     Pick: Hannover U23 – Erzgebirge Aue / Over 2.5
     Unit size: 2 units
     Write Up: This pick is from my soccer model that I've been using for the past two years. It assigns ELO ratings to players and projects a win chance based on the combined ELO ratings of the players on each team. TeamReddit is projecting a 62% win chance here which creates value here on the ML.

    Note: The example above is just a template. The actual suggestions will vary in format and content.
     
    # OBJECTIVE #
    You need to review all the suggestions carefully. Examine each author's track record and evaluate the reasoning behind their bets. Then, use your knowledge of the latest information about the teams/players involved in the match to determine the best bet for today.
    Remember to incorporate your knowledge obtained from the internet as well.
    Suggestions with detailed reasoning and a strong track record should be given greater weight.
    If multiple authors are betting on the same sporting event and their bets are not on opposing teams, those bets should be prioritized.
    However, if multiple authors are betting on the same event but on opposing teams, consider the event as risky.
    Aim to provide a single best bet, but if you believe there are a few bets of equal quality, include all of them.   
     
    # STYLE #
    A check mark or anything that has the same meaning usually means that it is a win.
    A cross mark or anything that has the same meaning usually means that it is a loss.
     
    # TONE #
    Brief
     
    # RESPONSE #
    Each response must clearly specify what to bet on and identify the author of the bet.
    You must also provide your own input, based on your research, explaining why you agree with the author and include their track record.
    When you provide the bet(s), ensure they are from the most recent suggestions based on the date and pertain to sporting events that have not yet occurred.
    Check the results of the sporting events before offering the bet. If the event has already taken place, do not include it in your response.
    If there are multiple bets, present them as bullet points."""
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
    query = "What are the best bet(s) for today or tomorrow?"
    
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
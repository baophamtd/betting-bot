import sys
import os
import datetime
import json
import re
from typing import List, Dict, Any, Tuple

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from helpers.tools.reddit_parser import RedditParser
from helpers.tools.openai_client import OpenAIClient
from helpers.tools.telegram_bot_client import TelegramBotClient

class AppIdeasBot:
    def __init__(self):
        self.reddit_parser = RedditParser()
        self.openai_client = OpenAIClient()
        self.telegram_client = TelegramBotClient()
        self.subreddit = "AppIdeas"
        
    def get_posts_from_past_24_hours(self) -> List[Any]:
        """
        Fetch all posts from r/AppIdeas from the past 24 hours.
        
        :return: A list of Reddit post objects
        """
        print(f"Fetching posts from r/{self.subreddit} from the past 24 hours...")
        posts = self.reddit_parser.get_posts_from_subreddit_in_past_24_hours(self.subreddit)
        print(f"Found {len(posts)} posts from the past 24 hours")
        return posts
    
    def format_post_for_analysis(self, post) -> Dict[str, Any]:
        """
        Format a Reddit post for OpenAI analysis.
        Extracts both title and content (selftext) from each post.
        
        :param post: A PRAW submission object
        :return: A dictionary containing formatted post data
        """
        # Get the post content - this could be selftext for text posts or URL for link posts
        content = ""
        if hasattr(post, 'selftext') and post.selftext:
            content = post.selftext
        elif hasattr(post, 'url') and post.url:
            content = f"Link: {post.url}"
        
        return {
            "title": post.title,
            "content": content,
            "url": post.url if hasattr(post, 'url') else "",
            "author": str(post.author) if post.author else "Unknown",
            "created_utc": datetime.datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "score": post.score,
            "num_comments": post.num_comments,
            "permalink": f"https://reddit.com{post.permalink}",
            "post_type": "text" if hasattr(post, 'selftext') and post.selftext else "link"
        }
    
    def analyze_idea_with_gpt5(self, post_data: Dict[str, Any]) -> str:
        """
        Analyze an app idea using OpenAI GPT-5 with optimized speed settings.
        
        :param post_data: Formatted post data
        :return: GPT-5's analysis of the idea
        """
        input_text = f"""
        Analyze this app idea from r/AppIdeas:

        **Title:** {post_data['title']}
        **Content:** {post_data['content']}
        **Score:** {post_data['score']} upvotes | **Comments:** {post_data['num_comments']}

        Rate each criterion (1-10) with brief explanation:
        1. **Feasibility** - Technical difficulty
        2. **Market Potential** - Demand/opportunity  
        3. **Innovation** - Uniqueness
        4. **Monetization** - Revenue potential
        5. **AI Integration** - AI/ML usage (PRIORITIZE AI ideas)
        6. **Overall Viability** - Overall potential

        IMPORTANT: Prioritize AI-powered ideas. Non-AI ideas should score lower unless exceptional.

        Provide:
        - Brief summary (1-2 sentences)
        - Top 3 scores with short explanations
        - Key strength/weakness (1 each)
        - Recommendation: Pursue/Consider/Pass

        Keep response under 200 words.
        """
        
        try:
            # Use GPT-5 with Chat Completions API
            response = self.openai_client.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": "You are an expert app developer and business analyst who evaluates app ideas for feasibility and market potential."},
                    {"role": "user", "content": input_text}
                ],
                max_completion_tokens=3000  # Much higher limit for GPT-5 reasoning + response
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error analyzing idea with GPT-5: {e}")
            return f"Error analyzing idea: {str(e)}"
    
    def filter_feasible_ideas(self, posts_with_analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter posts to only include those with feasible ideas based on GPT-5 analysis.
        Only includes ideas with AI Integration score of 5 or higher.
        
        :param posts_with_analysis: List of posts with their GPT-5 analysis
        :return: List of posts that are deemed feasible
        """
        feasible_ideas = []
        
        for post_data in posts_with_analysis:
            analysis = post_data.get('analysis', '')
            
            # First check if AI Integration score is 7 or higher
            ai_score = self._extract_ai_score(analysis)
            print(f"🤖 AI Integration Score: {ai_score}/10")
            if ai_score < 7:
                print(f"❌ Filtered out: AI score {ai_score} < 7")
                continue  # Skip ideas with low AI integration
            else:
                print(f"✅ Passed AI filter: AI score {ai_score} >= 7")
            
            # Look for positive indicators in the analysis
            positive_indicators = [
                'pursue', 'feasible', 'viable', 'promising', 'good potential',
                'market demand', 'innovative', 'monetizable', 'recommend',
                'ai', 'machine learning', 'automation', 'artificial intelligence'
            ]
            
            # Look for high scores (8+ or 9+) and AI integration
            high_score_patterns = [
                r'feasibility.*[89]', r'market potential.*[89]', 
                r'innovation.*[89]', r'monetization.*[89]',
                r'ai integration.*[89]', r'overall viability.*[89]'
            ]
            
            is_feasible = False
            
            # Check for positive indicators
            analysis_lower = analysis.lower()
            for indicator in positive_indicators:
                if indicator in analysis_lower:
                    is_feasible = True
                    break
            
            # Check for high scores
            if not is_feasible:
                for pattern in high_score_patterns:
                    if re.search(pattern, analysis_lower):
                        is_feasible = True
                        break
            
            if is_feasible:
                feasible_ideas.append(post_data)
        
        return feasible_ideas
    
    def format_telegram_message(self, feasible_ideas: List[Dict[str, Any]], total_posts: int) -> str:
        """
        Format the feasible ideas into a Telegram message.
        
        :param feasible_ideas: List of feasible ideas
        :param total_posts: Total number of posts analyzed
        :return: Formatted message string
        """
        if not feasible_ideas:
            return f"📱 **AppIdeas Daily Report** - {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n" \
                   f"📊 Analyzed {total_posts} posts from r/AppIdeas in the past 24 hours\n\n" \
                   f"🤖 No AI-powered ideas found today (AI score ≥7 required).\n\n" \
                   f"Better luck tomorrow! 🍀"
        
        message = f"📱 **AppIdeas Daily Report** - {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n"
        message += f"📊 Analyzed {total_posts} posts from r/AppIdeas in the past 24 hours\n"
        message += f"🤖 Found {len(feasible_ideas)} AI-powered ideas (AI score ≥7)!\n\n"
        
        return message
    
    def format_individual_idea_message(self, idea: Dict[str, Any], idea_number: int) -> str:
        """
        Format a single idea into a detailed Telegram message.
        
        :param idea: Idea data with analysis
        :param idea_number: Number of the idea (1, 2, 3, etc.)
        :return: Formatted message string for this idea
        """
        message = f"**{idea_number}. {idea['title']}**\n"
        message += f"👤 u/{idea['author']} | ⬆️ {idea['score']} | 💬 {idea['num_comments']}\n"
        message += f"🔗 https://reddit.com{idea['permalink']}\n\n"
        
        # Extract detailed information from GPT-5 analysis
        analysis = idea['analysis']
        summary = self._extract_summary(analysis)
        scores = self._extract_scores(analysis)
        key_insights = self._extract_key_insights(analysis)
        
        # Add summary
        if summary:
            message += f"📝 **Summary:** {summary}\n\n"
        
        # Add detailed scorecards
        if scores:
            message += f"📊 **Scorecard:**\n"
            for score_name, score_value, reason in scores:
                message += f"• **{score_name}:** {score_value}/10 - {reason}\n"
            message += "\n"
        
        # Add key insights
        if key_insights:
            message += f"💡 **Key Insights:** {key_insights}\n\n"
        
        return message
    
    def _extract_summary(self, analysis: str) -> str:
        """Extract the brief summary from GPT-5 analysis."""
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if 'brief summary' in line.lower() or 'summary' in line.lower():
                # Look for the next non-empty line
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() and not lines[j].startswith('Scores'):
                        return lines[j].strip()
        return ""
    
    def _extract_scores(self, analysis: str) -> List[Tuple[str, str, str]]:
        """Extract scores and reasons from GPT-5 analysis."""
        scores = []
        lines = analysis.split('\n')
        
        for line in lines:
            if ':' in line and ('/10' in line or '/ 10' in line):
                # Extract score name, value, and reason
                parts = line.split(':', 1)
                if len(parts) == 2:
                    score_name = parts[0].strip().replace('-', '').strip()
                    score_part = parts[1].strip()
                    
                    # Extract score value
                    import re
                    score_match = re.search(r'(\d+)/10', score_part)
                    if score_match:
                        score_value = score_match.group(1)
                        # Extract reason (everything after the score)
                        reason = score_part.split(score_value + '/10', 1)[1].strip()
                        if reason.startswith('—'):
                            reason = reason[1:].strip()
                        elif reason.startswith('–'):
                            reason = reason[1:].strip()
                        
                        scores.append((score_name, score_value, reason))
        
        return scores
    
    def _extract_top_scores(self, analysis: str) -> str:
        """Extract only the top 2-3 scores for concise display."""
        scores = self._extract_scores(analysis)
        if not scores:
            return ""
        
        # Sort by score value (highest first)
        scores.sort(key=lambda x: int(x[1]), reverse=True)
        
        # Take top 2-3 scores and format concisely
        top_scores = scores[:3]
        formatted = []
        
        for score_name, score_value, reason in top_scores:
            # Shorten score name
            short_name = score_name.replace('Feasibility', 'Feas').replace('Market Potential', 'Market').replace('AI Integration', 'AI').replace('Overall Viability', 'Overall')
            # Truncate reason to 30 chars
            short_reason = reason[:30] + "..." if len(reason) > 30 else reason
            formatted.append(f"{short_name}: {score_value}/10 - {short_reason}")
        
        return " | ".join(formatted)
    
    def _extract_ai_score(self, analysis: str) -> int:
        """Extract the AI Integration score from GPT-5 analysis."""
        lines = analysis.split('\n')
        
        for line in lines:
            # Look for AI Integration score pattern
            if 'ai integration' in line.lower() and ('/10' in line or '/ 10' in line):
                import re
                score_match = re.search(r'(\d+)/10', line)
                if score_match:
                    return int(score_match.group(1))
        
        # If no AI Integration score found, return 0 (will be filtered out)
        return 0
    
    def _extract_key_insights(self, analysis: str) -> str:
        """Extract key insights from GPT-5 analysis."""
        lines = analysis.split('\n')
        insights = []
        
        # Look for key strengths, weaknesses, or opportunities
        for line in lines:
            if any(keyword in line.lower() for keyword in ['key strength', 'key weakness', 'opportunity', 'challenge']):
                if line.strip() and not line.startswith('Key'):
                    insights.append(line.strip())
        
        # Limit to 2-3 key insights to keep message concise
        return ' | '.join(insights[:3]) if insights else ""
    
    def run_daily_analysis(self):
        """
        Run the daily analysis of AppIdeas subreddit.
        """
        try:
            print("Starting AppIdeas daily analysis...")
            
            # Get posts from past 24 hours
            posts = self.get_posts_from_past_24_hours()
            
            if not posts:
                message = f"📱 **AppIdeas Daily Report** - {datetime.datetime.now().strftime('%Y-%m-%d')}\n\n" \
                         f"📊 No new posts found in r/AppIdeas in the past 24 hours.\n\n" \
                         f"Check back tomorrow! 🍀"
                self.telegram_client.send_message(message)
                return
            
            print(f"Analyzing {len(posts)} posts with GPT-5...")
            
            # Analyze each post
            posts_with_analysis = []
            for i, post in enumerate(posts, 1):
                print(f"Analyzing post {i}/{len(posts)}: {post.title[:50]}...")
                
                post_data = self.format_post_for_analysis(post)
                analysis = self.analyze_idea_with_gpt5(post_data)
                post_data['analysis'] = analysis
                posts_with_analysis.append(post_data)
                
                # Print full analysis to console
                print(f"\n{'='*80}")
                print(f"POST {i}: {post.title}")
                print(f"{'='*80}")
                print(f"Author: u/{post_data['author']} | Score: {post_data['score']} | Comments: {post_data['num_comments']}")
                print(f"Content: {post_data['content'][:200]}...")
                print(f"\nGPT-5 ANALYSIS:")
                print(analysis)
                print(f"{'='*80}\n")
            
            # Filter for feasible ideas
            print(f"\n{'='*80}")
            print("FILTERING RESULTS:")
            print(f"{'='*80}")
            feasible_ideas = self.filter_feasible_ideas(posts_with_analysis)
            
            # Send summary message first
            summary_message = self.format_telegram_message(feasible_ideas, len(posts))
            self.telegram_client.send_message(summary_message)
            
            # Send individual messages for each feasible idea
            for i, idea in enumerate(feasible_ideas, 1):
                individual_message = self.format_individual_idea_message(idea, i)
                self.telegram_client.send_message(individual_message)
                print(f"📤 Sent individual message for idea {i}: {idea['title'][:50]}...")
            
            print(f"\n📊 FINAL SUMMARY:")
            print(f"Total posts analyzed: {len(posts)}")
            print(f"AI-powered ideas found: {len(feasible_ideas)}")
            print(f"Success rate: {len(feasible_ideas)/len(posts)*100:.1f}%")
            print(f"Messages sent: {1 + len(feasible_ideas)} (1 summary + {len(feasible_ideas)} individual)")
            print(f"{'='*80}")
            
        except Exception as e:
            error_message = f"❌ **AppIdeas Bot Error**\n\n" \
                           f"An error occurred during daily analysis:\n{str(e)}\n\n" \
                           f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.telegram_client.send_message(error_message)
            print(f"Error in daily analysis: {e}")

def main():
    """
    Main function to run the AppIdeas bot.
    """
    bot = AppIdeasBot()
    bot.run_daily_analysis()

if __name__ == "__main__":
    main()

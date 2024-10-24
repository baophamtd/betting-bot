import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class OddsAPI:
    def __init__(self):
        self.api_key = os.getenv('ODDS_API_KEY')
        if not self.api_key:
            raise ValueError("ODDS_API_KEY not found in environment variables")
        self.base_url = "https://api.the-odds-api.com/v4/sports"

    def get_nfl_odds_bovada(self) -> List[Dict[Any, Any]]:
        url = f"{self.base_url}/americanfootball_nfl/odds"
        params = {
            "api_key": self.api_key,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american",
            "bookmakers": "bovada"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    def get_player_props(self, event_id: str, markets: str) -> List[Dict[Any, Any]]:
        url = f"{self.base_url}/americanfootball_nfl/events/{event_id}/odds"
        params = {
            "api_key": self.api_key,
            "regions": "us",
            "markets": markets,
            "oddsFormat": "american",
            "bookmakers": "bovada"
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            player_props = []
            for bookmaker in data.get('bookmakers', []):
                if bookmaker['key'] == 'bovada':
                    for market in bookmaker.get('markets', []):
                        player_props.append({
                            'key': market['key'],
                            'outcomes': market['outcomes']
                        })
            
            return player_props
        except requests.RequestException as e:
            print(f"Error fetching player props: {str(e)}")
            return []

# Usage example:
# odds_api = OddsAPI()
# nfl_odds = odds_api.get_nfl_odds_bovada()

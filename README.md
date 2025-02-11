# AI Betting Advisor Bot

## Overview

#### The AI Betting Advisor Bot is an advanced tool designed to assist users in making informed betting decisions. By leveraging a RAG-based OpenAI personal assistant, this bot analyzes various data sources to provide insights and recommendations for sports betting.

## Features

- **NFL Player Prop Analysis**: Extracts and analyzes player prop posts from Reddit to provide betting insights.
- **Odds Retrieval**: Fetches the latest NFL odds from Bovada using the OddsAPI.
- **Comment Analysis**: Iterates through Reddit comments to gather community opinions and trends.
- **Image to Text Conversion**: Utilizes OCR technology to convert images into text for further analysis.
- **Telegram Integration**: Sends updates and insights directly to your Telegram account.

## Components

- **Reddit Parser**: Gathers posts and comments from specified subreddits.
- **OddsAPI**: Interfaces with external APIs to retrieve betting odds.
- **OpenAI Client**: Leverages a RAG-based OpenAI personal assistant to generate betting advice and insights.
- **Telegram Bot Client**: Manages communication with Telegram for real-time updates.

## Getting Started

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd betting-bot
   ```

2. **Install Dependencies**:
   Ensure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   Create a `.env` file and add your API keys and tokens. Make sure to use your own credentials for each service:
   ```
   OCR_SPACE_API_KEY=your_ocr_api_key
   ODDS_API_KEY=your_odds_api_key
   OPENAI_API_KEY=your_openai_api_key
   BAO_TELEGRAM_ID=your_telegram_id
   BAO_TELEGRAM_TOKEN=your_telegram_token
   ```

4. **Run the Bot**:
   Execute the main script to start the bot:
   ```bash
   python main.py
   ```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License.

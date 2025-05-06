# Telegram Bot Backend

This is a template for a Telegram bot that processes user queries through an agentic system.

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the following variables:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
ALLOWED_USERS=user_id1,user_id2  # Optional: Comma-separated list of allowed Telegram user IDs
```

To get your bot token:
1. Talk to [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot using the `/newbot` command
3. Copy the token provided by BotFather

To get your Telegram user ID:
1. Talk to [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your user ID

## Running the Bot

1. Make sure your virtual environment is activated
2. Run the bot:
```bash
python bot.py
```

## Features

- User authentication (optional)
- Processes user queries through an agentic system
- Supports basic commands (/start, /help)
- Error handling and logging
- Typing indicators while processing queries

## Customization

To integrate your own agentic system:
1. Modify the `AgentHandler` class in `agent_handler.py`
2. Implement your processing logic in the `process_query` method
3. Add any necessary formatting in the `format_response` method

## File Structure

- `bot.py`: Main bot implementation
- `config.py`: Configuration and environment variables
- `agent_handler.py`: Agent system integration
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (create this file) 

## Youtube Link
Here is the youtube link for the [demo video](https://youtube.com)
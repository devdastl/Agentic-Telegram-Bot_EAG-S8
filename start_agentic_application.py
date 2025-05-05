import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram_backend.config import TELEGRAM_BOT_TOKEN, ALLOWED_USERS
from telegram_backend.agent_handler import AgentHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize the agent handler
agent = AgentHandler()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = str(update.effective_user.id)
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        logger.info(f"User {user_id} is not authorized to use this bot.")
        return

    welcome_message = (
        "👋 Welcome to the Agent Bot!\n\n"
        "You can send me any query, and I'll process it through our agent system.\n"
        "Just type your message, and I'll respond with the agent's answer.\n\n"
        "Available commands:\n"
        "/start - Show this welcome message\n"
        "/help - Show help information"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "🤖 Agent Bot Help\n\n"
        "Simply send me your query as a message, and I'll process it through the agent system.\n\n"
        "Tips:\n"
        "- Be clear and specific in your queries\n"
        "- Wait for the response before sending another query\n"
        "- Use /start to see the welcome message again"
    )
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages and process them through the agent."""
    user_id = str(update.effective_user.id)
    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    # Get the user's message
    user_message = update.message.text

    try:
        # Send a "typing" action while processing
        await update.message.chat.send_action(action="typing")
        
        # Process the query through the agent
        response = await agent.process_query(user_message)
        
        # Format the response
        formatted_response = await agent.format_response(response)
        
        # Send the response back to the user
        await update.message.reply_text(formatted_response)
        
    except Exception as e:
        error_message = f"Sorry, an error occurred while processing your request: {str(e)}"
        await update.message.reply_text(error_message)
        logger.error(f"Error processing message: {str(e)}")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 
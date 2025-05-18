# Discord Reminder Bot
# This is the main entry point for the application

# Import and start the web server
from src.web_server import start_web_server
start_web_server()

# Import the Discord bot from the src directory
import src.discord_bot

# The bot will be started automatically when imported

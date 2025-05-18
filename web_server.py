import os
import secrets
import hashlib
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_discord import DiscordOAuth2Session, requires_authorization
import discord
from dotenv import load_dotenv

from sqlalchemy_models import Database
from utilities import format_time, format_setting

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('web_server.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('web-server')

# Check for required environment variables
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:5000/callback')
DISCORD_BOT_TOKEN = os.getenv('TOKEN')  # Using the same token as the bot

if not all([DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, DISCORD_BOT_TOKEN]):
    logger.critical("Missing required environment variables. Please set DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET, and TOKEN in .env file.")
    exit(1)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))
app.config['DISCORD_CLIENT_ID'] = DISCORD_CLIENT_ID
app.config['DISCORD_CLIENT_SECRET'] = DISCORD_CLIENT_SECRET
app.config['DISCORD_REDIRECT_URI'] = DISCORD_REDIRECT_URI
app.config['DISCORD_BOT_TOKEN'] = DISCORD_BOT_TOKEN

# Initialize Discord OAuth
discord_oauth = DiscordOAuth2Session(app)

# Initialize database
db = Database("Discord")

# Fixed salt for URL generation
URL_SALT = os.getenv('URL_SALT', 'discord-at-code-reminder-salt-12345')

# Function to generate consistent server URL token
def generate_server_token(server_id: str) -> str:
    """
    Generate a consistent token for a server based on server ID and salt

    Args:
        server_id (str): Discord server ID

    Returns:
        str: Hashed token for server URL
    """
    # Combine server ID with salt
    combined = f"{server_id}:{URL_SALT}"
    # Create SHA-256 hash
    hash_obj = hashlib.sha256(combined.encode())
    # Return first 16 characters of the hex digest
    return hash_obj.hexdigest()[:16]

@app.route('/')
def index():
    """Home page with login button"""
    return render_template('index.html')

@app.route('/login')
def login():
    """Redirect to Discord OAuth"""
    return discord_oauth.create_session(scope=['identify', 'guilds'])

@app.route('/callback')
def callback():
    """Handle Discord OAuth callback"""
    try:
        discord_oauth.callback()
        return redirect(url_for('servers'))
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Log out user"""
    discord_oauth.revoke()
    session.clear()
    return redirect(url_for('index'))

@app.route('/servers')
@requires_authorization
def servers():
    """Show list of servers where the user has access"""
    user = discord_oauth.fetch_user()
    guilds = discord_oauth.fetch_guilds()

    # Use all guilds the user is a member of, not just admin guilds
    user_guilds = guilds

    # Generate tokens dictionary for template
    tokens = {guild.id: generate_server_token(str(guild.id)) for guild in user_guilds}

    return render_template('servers.html', user=user, guilds=user_guilds, server_tokens=tokens)

@app.route('/server/<server_id>/<token>')
def server_dashboard(server_id, token):
    """Server-specific dashboard with notifications"""
    # Verify token using the hash function directly
    expected_token = generate_server_token(server_id)
    if token != expected_token:
        abort(403)  # Forbidden

    # Get server notifications
    try:
        # Create table if it doesn't exist
        db.create_table(guild_id=server_id)

        # Get all notifications for this server
        notifications = db.get_all(guild_id=server_id)

        # Format notifications for display
        formatted_notifications = []
        for notification in notifications:
            formatted_notification = {
                "id": notification["id"],
                "channel_id": notification["channel_id"],
                "option": notification["option"],
                "title": notification["title"],
                "message": notification["main_text"],
                "time": format_time(
                    setting_type=notification["option"],
                    week=notification["week"],
                    day=notification["day"],
                    time=notification["call_time"]
                ),
                "mention_ids": notification["mention_ids"],
                "img": notification["img"]
            }
            formatted_notifications.append(formatted_notification)

        return render_template(
            'dashboard.html', 
            server_id=server_id, 
            token=token,
            notifications=formatted_notifications
        )
    except Exception as e:
        logger.error(f"Error fetching notifications for server {server_id}: {e}")
        flash('Error fetching notifications. Please try again.', 'error')
        return redirect(url_for('servers'))

@app.route('/server/<server_id>/<token>/add', methods=['GET', 'POST'])
def add_notification(server_id, token):
    """Add a new notification"""
    # Verify token using the hash function directly
    expected_token = generate_server_token(server_id)
    if token != expected_token:
        abort(403)  # Forbidden

    if request.method == 'POST':
        try:
            option = request.form['option']
            channel_id = request.form['channel_id']
            title = request.form['title']
            message = request.form['message']
            time = request.form['time']
            mention_ids = request.form.get('mention_ids', 'None')
            img = request.form.get('img', 'None')

            # Set day and week based on option
            day = 'None'
            week = 'None'

            if option == 'oneday':
                day = request.form['day']
            elif option == 'week':
                week = request.form['week']
            elif option == 'month':
                day = request.form['day']
                if 'week' in request.form:
                    week = request.form['week']

            # Validate time format
            datetime.strptime(time, '%H:%M:%S')

            # Add notification to database
            db.set(
                guild_id=server_id,
                channel_id=channel_id,
                option=option,
                day=day,
                week=week,
                call_time=time,
                mention_ids=mention_ids,
                title=title,
                main_text=message,
                img=img
            )

            flash('Notification added successfully!', 'success')
            return redirect(url_for('server_dashboard', server_id=server_id, token=token))
        except Exception as e:
            logger.error(f"Error adding notification: {e}")
            flash(f'Error adding notification: {str(e)}', 'error')

    return render_template('add_notification.html', server_id=server_id, token=token)

@app.route('/server/<server_id>/<token>/edit/<notification_id>', methods=['GET', 'POST'])
def edit_notification(server_id, token, notification_id):
    """Edit an existing notification"""
    # Verify token using the hash function directly
    expected_token = generate_server_token(server_id)
    if token != expected_token:
        abort(403)  # Forbidden

    # Get notification
    notification = db.get(guild_id=server_id, id=notification_id)
    if not notification:
        flash('Notification not found.', 'error')
        return redirect(url_for('server_dashboard', server_id=server_id, token=token))

    if request.method == 'POST':
        try:
            channel_id = request.form['channel_id']
            title = request.form['title']
            message = request.form['message']
            time = request.form['time']
            mention_ids = request.form.get('mention_ids', 'None')
            img = request.form.get('img', 'None')

            # Update notification in database
            db.update_setting_time(
                guild_id=server_id,
                id=notification_id,
                channel_id=channel_id,
                call_time=time,
                mention_ids=mention_ids,
                title=title,
                main_text=message,
                img=img
            )

            flash('Notification updated successfully!', 'success')
            return redirect(url_for('server_dashboard', server_id=server_id, token=token))
        except Exception as e:
            logger.error(f"Error updating notification: {e}")
            flash(f'Error updating notification: {str(e)}', 'error')

    return render_template('edit_notification.html', server_id=server_id, token=token, notification=notification)

@app.route('/server/<server_id>/<token>/delete/<notification_id>')
def delete_notification(server_id, token, notification_id):
    """Delete a notification"""
    # Verify token using the hash function directly
    expected_token = generate_server_token(server_id)
    if token != expected_token:
        abort(403)  # Forbidden

    try:
        db.delete(guild_id=server_id, id=notification_id)
        flash('Notification deleted successfully!', 'success')
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        flash(f'Error deleting notification: {str(e)}', 'error')

    return redirect(url_for('server_dashboard', server_id=server_id, token=token))

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)

    # Run the app
    app.run(debug=True)

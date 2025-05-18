import os
import threading
from flask import Flask

# Initialize Flask app
app = Flask(__name__)

# Define route for the home page
@app.route('/')
def home():
    return "Discord Reminder Bot is running!"

# Define route for health check
@app.route('/health')
def health():
    return "OK", 200

# Function to run the web server
def run_web_server():
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 8080))
    # Run the Flask app
    app.run(host='0.0.0.0', port=port)

# Function to start the web server in a separate thread
def start_web_server():
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True  # This ensures the thread will close when the main program exits
    web_thread.start()
    print(f"Web server started on port {int(os.environ.get('PORT', 8080))}")
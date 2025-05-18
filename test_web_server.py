import requests
import time
import sys

def test_web_server():
    """
    Test if the web server is running by making a request to the health endpoint.
    """
    print("Testing web server...")
    try:
        # Wait a bit for the server to start
        time.sleep(2)
        
        # Make a request to the health endpoint
        response = requests.get('http://localhost:8080/health')
        
        # Check if the response is OK
        if response.status_code == 200 and response.text == 'OK':
            print("Web server is running correctly!")
            return True
        else:
            print(f"Web server returned unexpected response: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("Could not connect to web server. Make sure it's running on port 8080.")
        return False
    except Exception as e:
        print(f"Error testing web server: {e}")
        return False

if __name__ == "__main__":
    print("This script tests if the web server is running.")
    print("To run the test, first start the bot with 'python main.py' in another terminal.")
    print("Then run this script with 'python test_web_server.py'.")
    
    # Ask for confirmation
    if input("Do you want to proceed with the test? (y/n): ").lower() != 'y':
        print("Test cancelled.")
        sys.exit(0)
    
    # Run the test
    success = test_web_server()
    
    if success:
        print("\nTest passed! The web server is running correctly.")
        print("This means the bot should stay alive on Replit.")
    else:
        print("\nTest failed! The web server is not running correctly.")
        print("Check your implementation and try again.")
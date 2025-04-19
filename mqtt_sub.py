import paho.mqtt.client as mqtt
import webbrowser
import subprocess
import json
from imdb import imdb_search
import datetime
import time
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("mqtt_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mqtt_client")

# Configuration
MQTT_TOPIC_TEST = "expo/test"       # Topic to receive messages from EXPO app
MQTT_TOPIC_RESULT = "expo/result"   # Topic to send results back to EXPO app
MQTT_TOPIC_STATUS = "expo/status"   # Topic for status updates
MQTT_BROKER = "192.168.31.9"        # Broker IP address
MQTT_PORT = 1883                    # Standard MQTT port (not WebSocket)
RECONNECT_DELAY = 5                 # Seconds to wait before reconnection attempts

def log_status(client, status_message, level=logging.INFO):
    """Log status message and publish to status topic"""
    logger.log(level, status_message)
    if client and client.is_connected():
        client.publish(MQTT_TOPIC_STATUS, status_message)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        log_status(client, f"Connected to MQTT broker at {MQTT_BROKER}")
        
        # Subscribe to both test and result topics
        client.subscribe(MQTT_TOPIC_TEST)
        log_status(client, f"Subscribed to topic: {MQTT_TOPIC_TEST}")
        
        client.subscribe(MQTT_TOPIC_RESULT)
        log_status(client, f"Subscribed to topic: {MQTT_TOPIC_RESULT}")
        
        # Publish a connection notification
        client.publish(MQTT_TOPIC_STATUS, "Backend connected and ready")
    else:
        connection_codes = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        error_msg = connection_codes.get(rc, f"Unknown error code {rc}")
        log_status(None, f"Connection failed: {error_msg}", logging.ERROR)

def on_disconnect(client, userdata, rc, properties=None):
    if rc != 0:
        log_status(None, f"Unexpected disconnection. Will reconnect in {RECONNECT_DELAY} seconds...", logging.WARNING)
        time.sleep(RECONNECT_DELAY)
        try:
            client.reconnect()
        except Exception as e:
            log_status(None, f"Reconnection failed: {e}", logging.ERROR)

def on_message(client, userdata, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    topic = message.topic
    msg_content = str(message.payload.decode("utf-8"))
    
    log_status(client, f"Received message on {topic}: {msg_content}")
    
    # Only process messages from the test topic
    if topic == MQTT_TOPIC_TEST:
        # Process message based on content
        if msg_content.startswith("open:"):
            # Extract URL and send it back to client to open
            url = msg_content[5:]  # Remove "open:" prefix
            log_status(client, f"Sending URL to client: {url}")
            # Send URL back to EXPO app for opening on the client device
            client.publish(MQTT_TOPIC_RESULT, f"open_url:{url}")
            
        elif msg_content.startswith("imdb:"):
            # Extract movie name and search IMDB
            movie_name = msg_content[5:]  # Remove "imdb:" prefix
            log_status(client, f"Searching IMDB for: {movie_name}")
            try:
                content = imdb_search(movie_name)
                
                # Make sure we have a URL to open
                if 'url_content' in content and content['url_content']:
                    # Add open_url directive to the result
                    content['open_url'] = content['url_content']
                    log_status(client, f"Sending movie URL to client: {content['url_content']}")
                    
                    # First, send a specific command to open the URL immediately
                    # This ensures the URL opens even if JSON parsing fails
                    client.publish(MQTT_TOPIC_RESULT, f"open_url:{content['url_content']}")
                    
                    # Then send the full content data
                    time.sleep(0.5)  # Small delay to separate messages
                    client.publish(MQTT_TOPIC_RESULT, json.dumps(content))
                    log_status(client, f"IMDB results published to {MQTT_TOPIC_RESULT}")
                else:
                    # If no URL found, just send the content
                    client.publish(MQTT_TOPIC_RESULT, json.dumps(content))
                    log_status(client, "IMDB results have no URL to open")
            except Exception as e:
                error_msg = f"Error searching IMDB: {e}"
                log_status(client, error_msg, logging.ERROR)
                client.publish(MQTT_TOPIC_RESULT, json.dumps({"error": error_msg}))
        
        # Process any other message types as needed
        else:
            log_status(client, f"Standard message received: {msg_content}")
            # Echo the message back to confirm receipt
            client.publish(MQTT_TOPIC_RESULT, f"Received: {msg_content}")
    
    # For messages on result topic, just log them
    elif topic == MQTT_TOPIC_RESULT:
        log_status(client, f"Result message detected (no further action needed)")

# Note: The DeprecationWarning about callback_api_version=VERSION1 is acknowledged
# but kept for compatibility. Future updates should use the latest API version.
try:
    # For Paho MQTT v2.0 or higher
    client = mqtt.Client(client_id="PythonSubscriber", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    logger.info("Created MQTT client using V2 API (note: CallbackAPIVersion.VERSION1 is deprecated)")
except (ValueError, AttributeError):
    # Fallback for older Paho MQTT versions
    try:
        client = mqtt.Client("PythonSubscriber")
        logger.info("Created MQTT client using V1 API")
    except Exception as e:
        logger.error(f"Failed to create MQTT client: {e}")
        raise

client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Set up last will message (sent if client disconnects unexpectedly)
client.will_set(MQTT_TOPIC_STATUS, "Backend disconnected unexpectedly", qos=1, retain=False)

# Connect to the broker
try:
    logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    # Start the loop
    client.loop_forever()
except Exception as e:
    logger.error(f"Failed to connect to MQTT broker: {e}")
    logger.error("Please check:")
    logger.error("1. Is the MQTT broker running?")
    logger.error("2. Is the IP address correct? (Current: {MQTT_BROKER})")
    logger.error("3. Is port {MQTT_PORT} accessible?")
    logger.error("4. Is there a firewall blocking the connection?")
    logger.error("5. Paho MQTT compatibility: Check your paho-mqtt version using 'pip show paho-mqtt'")


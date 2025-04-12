import paho.mqtt.client as mqtt
import webbrowser
import subprocess
import json
from aliexpress import aliexpress_search
import datetime
import time

# Configuration
MQTT_TOPIC = "expo/test"  # Updated to match the EXPO app's topic
MQTT_BROKER = "192.168.31.9"  # Updated to the local broker IP
MQTT_PORT = 1883  # Standard MQTT port (not WebSocket)
RECONNECT_DELAY = 5  # Seconds to wait before reconnection attempts

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connected to MQTT broker at {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to topic: {MQTT_TOPIC}")
        # Publish a connection notification
        client.publish("expo/status", "Backend connected")
    else:
        connection_codes = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized"
        }
        error_msg = connection_codes.get(rc, f"Unknown error code {rc}")
        print(f"Connection failed: {error_msg}")

def on_disconnect(client, userdata, rc, properties=None):
    if rc != 0:
        print(f"Unexpected disconnection. Will reconnect in {RECONNECT_DELAY} seconds...")
        time.sleep(RECONNECT_DELAY)
        try:
            client.reconnect()
        except Exception as e:
            print(f"Reconnection failed: {e}")

def on_message(client, userdata, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg_content = str(message.payload.decode("utf-8"))
    print(f"[{timestamp}] Received message on {message.topic}: {msg_content}")
    
    # Process message based on content
    if msg_content.startswith("open:"):
        # Extract URL and open in browser
        url = msg_content[5:]  # Remove "open:" prefix
        print(f"Opening URL: {url}")
        webbrowser.open(url)
        # Send confirmation back to EXPO app
        client.publish("expo/result", f"Opened URL: {url}")
        
    elif msg_content.startswith("ali:"):
        # Extract product name and search AliExpress
        product_name = msg_content[4:]  # Remove "ali:" prefix
        print(f"Searching AliExpress for: {product_name}")
        try:
            content = aliexpress_search(product_name)
            # Publish result back to MQTT as JSON
            client.publish("expo/result", json.dumps(content))
            print(f"AliExpress results published to expo/result")
        except Exception as e:
            error_msg = f"Error searching AliExpress: {e}"
            print(error_msg)
            client.publish("expo/result", json.dumps({"error": error_msg}))
    
    # Process any other message types as needed
    else:
        print(f"Standard message received: {msg_content}")
        # Echo the message back to confirm receipt
        client.publish("expo/result", f"Received: {msg_content}")

# Initialize MQTT client with callback API version parameter
try:
    # For Paho MQTT v2.0 or higher
    client = mqtt.Client(client_id="PythonSubscriber", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    print("Created MQTT client using V2 API")
except (ValueError, AttributeError):
    # Fallback for older Paho MQTT versions
    try:
        client = mqtt.Client("PythonSubscriber")
        print("Created MQTT client using V1 API")
    except Exception as e:
        print(f"Failed to create MQTT client: {e}")
        raise

client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Set up last will message (sent if client disconnects unexpectedly)
client.will_set("expo/status", "Backend disconnected", qos=1, retain=False)

# Connect to the broker
try:
    print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    # Start the loop
    client.loop_forever()
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")
    print("Please check:")
    print("1. Is the MQTT broker running?")
    print("2. Is the IP address correct?")
    print("3. Is port 1883 accessible?")
    print("4. Is there a firewall blocking the connection?")
    print("5. Paho MQTT compatibility: Check your paho-mqtt version using 'pip show paho-mqtt'")


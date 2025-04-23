# EXPO and MQTT Integration Lab

## ✅ Lab Completion Status
**COMPLETED**: Both Lab 4 and Lab 5 tasks have been successfully implemented and tested.

## 📑 Full Project Report
The complete project report documenting both Lab 4 (EXPO and MQTT Integration) and Lab 5 (System Information and Monitoring) is available here:

👉 [**View Detailed Project Report**](report.md)

The report includes:
- Detailed implementation steps for both labs
- System information and monitoring results
- Screenshots and technical explanations
- Troubleshooting tips and solutions

## Objective
Integrate an EXPO mobile application with an MQTT server and connect a backend subscriber that listens to messages from the EXPO app.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Setup Using Distrobox](#setup-using-distrobox)
- [MQTT Broker Configuration](#mqtt-broker-configuration)
- [Running the EXPO App](#running-the-expo-app)
- [Backend Integration](#backend-integration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Understanding MQTT Port Differences](#understanding-mqtt-port-differences)

## Prerequisites
- Host system with Distrobox installed
- MQTTX client (for testing)
- Node.js and npm
- Python 3
- Network access (preferably mobile hotspot for internal network testing)

## Setup Using Distrobox

### 1. Create an Ubuntu Container
```bash
# Create a new Ubuntu container with systemd support
distrobox create --name mqtt-lab --image ubuntu:22.04 --init --additional-packages="systemd systemd-sysv"

# Enter the container
distrobox enter mqtt-lab

# Enable systemd within the container (if needed)
sudo systemctl daemon-reload
```

### 2. Update and Install Required Packages
```bash
# Update package lists and upgrade existing packages
sudo apt update && sudo apt upgrade -y

# Install Mosquitto, clients, and other utilities
sudo apt install mosquitto mosquitto-clients vim net-tools -y

# Enable and start Mosquitto service
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

## MQTT Broker Configuration

### 1. Configure Mosquitto MQTT Broker
```bash
# Open the configuration file
sudo vim /etc/mosquitto/mosquitto.conf
```

Replace the content with:
```
# Place your local configuration in /etc/mosquitto/conf.d/
#
# A full description of the configuration file is at
# /usr/share/doc/mosquitto/examples/mosquitto.conf.example

#pid_file /run/mosquitto/mosquitto.pid
listener 1883
listener 8000
protocol websockets
allow_anonymous true
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
include_dir /etc/mosquitto/conf.d
```

### 2. Restart Mosquitto Service
```bash
sudo systemctl restart mosquitto
```

### 3. Verify Mosquitto is Running
```bash
# Check if Mosquitto is listening on the configured ports
sudo netstat -tulnp | grep mosquitto

# Find your IP address
ip r
```

## Running the EXPO App  

### 1. Download and Extract EXPO App
Download the EXPO application from Moodle and extract it to your working directory:

```bash
# Extract the EXPO app
unzip mqtt-app.zip -d mqtt-app
cd mqtt-app
```

### 2. Configure MQTT Connection
Update the MQTT connection in the `hooks/useMQTTConnection.ts` file to use your MQTT broker's IP address and port 8000 (WebSocket):

```typescript
// Find this section in hooks/useMQTTConnection.ts
const client = new Paho.MQTT.Client(
  '192.168.60.254',  // Your actual IP address
  8000,           // WebSocket port
  `expo-mqtt-${Math.random().toString(16).substr(2, 8)}`
);
```

The EXPO app includes functionality to:
- Handle direct URL opening with `open_url:` prefix messages
- Process JSON formatted responses from the backend
- Support multiple URL formats in responses
- Open links using either WebBrowser or system Linking as fallback

### 3. Install Dependencies and Start the EXPO App
```bash
# Install dependencies
npm install

# Start the EXPO app
npx expo start
```

### 4. Connect with Mobile Device
- Install the Expo Go app on your mobile device
- Scan the QR code displayed in the terminal
- Ensure your mobile device is connected to the same network as your MQTT broker

## Backend Integration

### 1. Install Python Dependencies
The Python backend requires several packages to function correctly:

```bash
# Install required Python packages
pip install -r requirements.txt
```

Alternatively, you can install them individually:
```bash
pip install paho-mqtt selenium webdriver_manager beautifulsoup4 requests
```

### 2. Configure Python Backend
The Python backend consists of two main files:
- `mqtt_sub.py`: Handles MQTT communication and message processing
- `imdb.py`: Provides movie search functionality via web scraping

Ensure both files are in the same directory. The `mqtt_sub.py` script imports functions from `imdb.py`.

Update the MQTT broker connection in `mqtt_sub.py` to match your network configuration:

```python
# Configuration
MQTT_TOPIC = "expo/test"     # Must match the topic used in the EXPO app
MQTT_BROKER = "192.168.x.x"  # Replace with your actual broker IP
MQTT_PORT = 1883             # Standard MQTT port (NOT the WebSocket port)
```

#### Note About Paho MQTT v2.0 Compatibility
If you encounter this error:
```
ValueError: Unsupported callback API version: version 2.0 added a callback_api_version, see docs/migrations.rst for details
```

It means you're using Paho MQTT v2.0+, which requires a callback API version parameter. The script includes a compatibility fix with the following client initialization:

```python
client = mqtt.Client(client_id="PythonSubscriber", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
```

### Improved IMDB Search Functionality
The IMDB search functionality has been enhanced to use a multi-layered approach:

1. **Primary Method**: Uses Selenium to navigate to search results and extract structured data
2. **Direct Search URL**: If regular search fails, tries a more direct search URL approach
3. **Fallback Method**: If Selenium approaches fail, uses a requests/BeautifulSoup based approach
4. **Error Recovery**: Includes multiple fallback mechanisms to ensure some results are always returned

This makes the search more reliable across different network conditions and IMDB website updates.

### 3. Run the Python Backend
Start the Python backend subscriber with:

```bash
python3 mqtt_sub.py
```

You should see confirmation messages when the script:
- Connects to the MQTT broker
- Subscribes to the "expo/test" topic
- Starts listening for messages

### 4. Supported Commands
The Python backend recognizes special command formats in messages:

| Command Format | Example | Action |
|----------------|---------|--------|
| `open:URL` | `open:https://google.com` | Opens the specified URL in your default browser |
| `imdb:MOVIE_NAME` | `imdb:The Matrix` | Searches IMDB for the movie and opens results |
| Any other text | `Hello World` | Logs the message with timestamp |

All results and confirmations are published back to the `expo/result` topic for two-way communication.

## Verification

1. Connect all devices to the same network (preferably use your phone's hotspot)
2. Use MQTTX or another MQTT client to monitor communications:
   - Protocol: mqtt:// (for port 1883) or ws:// (for port 8000)
   - Host: Your broker IP address
   - Port: 1883 or 8000 depending on the protocol
   - Topic: `expo/test` and `expo/result`
   
3. Testing flow:
   - Send a message from the EXPO app with text "Hello World"
   - Verify it appears in MQTTX and the Python console
   - Send a message "open:https://www.google.com"
   - Verify a browser opens on your system
   - Send a message "imdb:The Matrix"
   - Verify IMDB search runs and browser opens with results
   - Check for response on the `expo/result` topic

## Troubleshooting

- **Connection Issues**: Ensure both devices are on the same network
- **Port Access**: Check if the ports are accessible using `telnet [IP] [PORT]`
- **Log Files**: Check Mosquitto logs at `/var/log/mosquitto/mosquitto.log`
- **Firewall**: Check if firewall is blocking the ports
  ```bash
  sudo ufw status
  # If active, allow the ports
  sudo ufw allow 1883
  sudo ufw allow 8000
  ```

## Understanding MQTT Port Differences

### Port 1883 vs Port 8000

- **Port 1883**: Standard MQTT protocol
  - Uses TCP/IP directly
  - More efficient with lower overhead
  - Better for IoT devices and native applications
  - Cannot be used by web browsers directly

- **Port 8000 (WebSockets)**:
  - Encapsulates MQTT within WebSocket protocol
  - Allows web browsers to connect to MQTT
  - Slightly higher overhead
  - Necessary for web applications including EXPO apps running in a browser

When using the EXPO application, WebSocket connection (port 8000) is required for browser compatibility, while the Python backend can use the standard MQTT protocol (port 1883) for better efficiency.

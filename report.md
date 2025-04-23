# Laboratory Work: EXPO and MQTT Integration

## Overview of Completed Tasks
This report documents the successful completion of both Lab 4 (EXPO and MQTT Integration) and Lab 5 (System Information and Monitoring). Both laboratory tasks were implemented and tested successfully, creating a comprehensive IoT communication system with monitoring capabilities.

## Aim of the Work
1. To integrate the provided EXPO application with an MQTT server and connect a backend subscriber that listens to messages from the EXPO mobile app (Lab 4)
2. To implement system monitoring functionality that tracks system resources and responds to commands through MQTT (Lab 5)

## Environment Setup

For this lab, I opted to use Distrobox instead of VirtualBox as it provided a more lightweight containerization approach while maintaining full compatibility with the requirements.

### Container Creation

I created an Ubuntu 22.04 container using Distrobox:

```bash
distrobox create --name SmartDevices --image ubuntu:22.04
distrobox enter SmartDevices
```

### System Information
When running the setup script, the following system information was displayed:

```
===== System Information =====
Memory: 3063MB used / 3605MB total (84.97%)
Free memory: 247MB, Available: 541MB

Network Interfaces:
  lo:
    IPv4: 127.0.0.1
    IPv6: ::1
  wlp1s0:
    IPv4: 192.168.60.254
    IPv6: 2a00:1eb8:c051:98d3:e194:8255:145e:5943
    IPv6: fe80::2cc5:b545:553b:aa4a
```

The system monitor successfully detected and displayed memory usage and network interfaces with their respective IP addresses.

### MQTT Broker Installation and Configuration

Following the lab instructions, I installed the required packages:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install mosquitto mosquitto-clients vim net-tools -y
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

I then modified the Mosquitto configuration file at `/etc/mosquitto/mosquitto.conf` to match the requirements:

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

After configuring the broker, I restarted the service:

```bash
sudo systemctl restart mosquitto
```

### Verification of MQTT Broker Setup

I verified the Mosquitto server was listening on the correct ports:

```bash
sudo netstat -tulnp | grep mosquitto
```

The output confirmed the broker was operating correctly:

```
tcp        0      0 0.0.0.0:1883            0.0.0.0:*               LISTEN      7683/mosquitto      
tcp6       0      0 :::8000                 :::*                    LISTEN      7683/mosquitto      
tcp6       0      0 :::1883                 :::*                    LISTEN      7683/mosquitto
```

I identified my IP address using:

```bash
ip r
```

Which returned my IP as `192.168.31.9` on the network `192.168.31.0/24`.

## EXPO Application Integration

I extracted the provided EXPO application and configured it to connect to my MQTT broker:

```bash
unzip expo-mqtt-app.zip
cd mqtt-app
```

### Configuring MQTT Connection in EXPO

I modified the MQTT connection parameters in the `hooks/useMQTTConnection.ts` file:

```typescript
const client = new Paho.MQTT.Client(
  '192.168.31.9',  // Updated to my IP address
  8000,           // Using WebSocket port
  `expo-mqtt-${Math.random().toString(16).substr(2, 8)}`
);
```

I also enhanced the URL handling capabilities by implementing:
- Protocol verification (adding https:// when missing)
- Platform-specific opening strategies (web vs mobile)
- WebBrowser implementation for in-app browsing experience
- Fallback to system Linking when WebBrowser fails
- JSON parsing for structured data responses
- Multiple URL field detection from backend responses

### Running the EXPO Application

I started the EXPO application with:

```bash
npx expo start
```

The application successfully launched and displayed a QR code that could be scanned with the Expo Go app. The logs confirmed connection to the MQTT broker:

```
(NOBRIDGE) LOG  Connected to MQTT broker
(NOBRIDGE) LOG  Subscribing to expo/test
(NOBRIDGE) LOG  Successfully subscribed to expo/test
```

## Python Backend Integration

### Setting Up Dependencies

I installed the required Python packages:

```bash
pip install paho-mqtt selenium webdriver_manager beautifulsoup4 requests
```

### Configuring the MQTT Subscriber

I modified the provided `mqtt_sub.py` file to connect to my MQTT broker:

```python
# Configuration
MQTT_TOPIC_TEST = "expo/test"       # Topic to receive messages from EXPO app
MQTT_TOPIC_RESULT = "expo/result"   # Topic to send results back to EXPO app
MQTT_TOPIC_STATUS = "expo/status"   # Topic for status updates
MQTT_BROKER = "192.168.31.9"        # Broker IP address
MQTT_PORT = 1883                    # Standard MQTT port (not WebSocket)
```

I implemented sophisticated message handling including:
- Automatic reconnection with configurable delay
- Comprehensive error handling with meaningful messages
- Separate topics for commands, results, and status updates
- Last will message configuration for unexpected disconnections
- Status publishing to a dedicated topic for monitoring

### IMDB Search Functionality

A significant challenge was enhancing the IMDB search functionality, which initially just returned to the main page rather than providing specific movie information. I implemented a multi-layered approach in `imdb.py`:

1. Primary method using requests and BeautifulSoup to parse search results
2. Multiple selectors to handle IMDB's changing layout
3. Structured data extraction using JSON-LD when available
4. Fallbacks to ensure some results are always returned

This significantly improved the reliability of the movie search functionality, consistently returning detailed information instead of just the main page.

### Running the Backend

I started the Python backend with:

```bash
python mqtt_sub.py
```

The script confirmed successful connection:

```
Created MQTT client using V2 API
Connecting to MQTT broker at 192.168.31.9:1883...
Connected to MQTT broker at 192.168.31.9
Subscribed to topic: expo/test
```

## Lab 5: System Monitoring Implementation

In addition to the EXPO and MQTT integration from Lab 4, I successfully implemented the system monitoring features for Lab 5:

### System Monitor Features

1. **Command Processing System**: 
   - Created a robust command handling system that listens on the `expo/command` topic
   - Commands are processed and responses are sent back on `expo/response`
   - Status updates are published on `expo/status`

2. **File System Operations**:
   - Implemented directory listing functionality (`list_directory` command)
   - Added file creation capability (`create_file:filename|content` command)
   - Included security checks to prevent path traversal attacks

3. **System Information Collection**:
   - Memory usage reporting (`get_memory` command)
   - IP address information (`get_ip` command)
   - Automatic system information display at startup

4. **Integrated Startup Process**:
   - Single setup script that launches all components:
     - MQTT broker in Distrobox container
     - EXPO application
     - MQTT subscriber backend
     - System monitoring service

### Testing System Monitor Commands

I verified all system monitor commands worked correctly:

1. **List Directory**:
   Sending `list_directory` to `expo/command` returned a JSON response with:
   - Current working directory
   - List of files
   - File count
   - Status and timestamp

2. **Get IP Information**:
   Sending `get_ip` to `expo/command` returned:
   - Network interface names
   - IPv4 and IPv6 addresses for each interface
   - Address family information

3. **Get Memory Information**:
   Sending `get_memory` to `expo/command` returned:
   - Total, used, and free memory in MB
   - Shared, buffer/cache, and available memory
   - Percentage of memory used

4. **Create File**:
   Sending `create_file:test.txt|Hello World` to `expo/command` resulted in:
   - File creation with the specified content
   - Response with the full path, file size, and creation timestamp

### Improvements to System Robustness

I added several enhancements to ensure system reliability:

1. **Automatic Package Management**:
   - Detection of missing Python packages
   - Automatic installation of required dependencies
   - Graceful failure handling with user-friendly error messages

2. **API Version Compatibility**:
   - Support for both Paho MQTT v1 and v2 APIs
   - Automatic detection and adaptation to available API versions

3. **Error Handling**:
   - Comprehensive error handling for all operations
   - Descriptive error messages with timestamps
   - Proper cleanup on shutdown

## Results Achieved

### 1. End-to-End Communication

I successfully established bidirectional communication between the EXPO app and the Python backend:

1. **EXPO to Python**: Messages sent from the EXPO app were properly received by the Python subscriber, with timestamps recorded.
2. **Python to EXPO**: Responses were sent back to the `expo/result` topic and appeared in the EXPO app.

The system uses three distinct MQTT topics for complete communication:
- `expo/test`: Main channel for commands and messages from the app
- `expo/result`: Channel for results and responses from the backend
- `expo/status`: Monitoring channel for connection status and system messages

### 2. Command Handling

The backend successfully processed different message formats:

1. **URL Opening**: Messages with the format `open:URL` triggered the backend to open the specified URL in a browser. For example:
   ```
   [2025-04-12 16:20:15] Received message on expo/test: open:https://www.google.com
   Opening URL: https://www.google.com
   ```

2. **IMDB Searches**: Messages with the format `imdb:MOVIE_NAME` triggered movie searches, opening the relevant page and returning structured data:
   ```
   [2025-04-12 16:42:30] Received message on expo/test: imdb:Saw
   Searching IMDB for: Saw
   Using requests-based search method
   Opening movie URL: https://www.imdb.com/title/tt0387564/?ref_=fn_ttl_ttl_1
   Successfully extracted structured data for: Saw
   Search complete. Found: Saw
   IMDB results published to expo/result
   ```

3. **Regular Messages**: Any other text was logged with a timestamp and echoed back to confirm receipt.

The URL opening implementation features multiple layers of handling:
1. Direct URL opening with the `open_url:` prefix for immediate action
2. JSON data with embedded URL fields for richer content display
3. Multiple URL field detection (`open_url`, `url_content`, `url`, `link`) for maximum compatibility

### 3. Working Code Demonstration

The enhanced code successfully handles:

- **Connection Reliability**: Automatic reconnection if the connection is lost
- **Message Processing**: Parsing different message formats and executing appropriate actions
- **Data Extraction**: Reliable movie data extraction from IMDB using multiple methods
- **Error Handling**: Graceful recovery from errors with meaningful fallbacks

## Port Differences: 8000 vs. 1883

A key aspect of this lab was understanding the differences between connecting to the MQTT broker via port 8000 (WebSocket) and port 1883 (standard MQTT):

### Standard MQTT (Port 1883)

Standard MQTT operates directly over TCP/IP and is optimized for machine-to-machine communication:

- **Implementation**: Direct TCP socket connection
- **Efficiency**: Lower overhead as it doesn't require additional protocol layers
- **Usage**: Ideal for IoT devices, embedded systems, and native applications
- **Security**: Often used with TLS (port 8883) for encrypted communication
- **Limitations**: Cannot be accessed directly from web browsers

In this lab, the Python backend used port 1883 because:
1. It ran as a native application with direct socket access
2. It benefited from the lower overhead and better efficiency
3. It didn't need browser compatibility

### WebSocket MQTT (Port 8000)

WebSocket MQTT encapsulates MQTT messages within the WebSocket protocol:

- **Implementation**: Uses HTTP upgrade to establish a WebSocket connection
- **Overhead**: Additional protocol headers and handshaking
- **Browser Compatibility**: Specifically designed for web browsers
- **Addressing**: Uses ws:// or wss:// (secure) URL schema
- **Integration**: Works with web frameworks and browser security models

The EXPO application required WebSocket MQTT (port 8000) because:
1. EXPO uses web technologies that follow browser security models
2. Web views cannot establish direct TCP socket connections
3. WebSockets provide the necessary compatibility layer

Understanding this distinction was crucial for proper configuration of the Mosquitto broker to support both connection types simultaneously, enabling a complete end-to-end system.

## Conclusion

This laboratory work successfully demonstrated:
1. Setting up and configuring an MQTT broker with both standard and WebSocket support
2. Integrating an EXPO application with the MQTT broker using WebSockets
3. Implementing a Python backend subscriber that listens for and processes messages
4. Establishing bidirectional communication between the components
5. Executing different actions based on received messages
6. Collecting and reporting system information through MQTT commands
7. Implementing file system operations via MQTT
8. Understanding the key differences between MQTT protocols

Both Lab 4 and Lab 5 tasks were completed successfully, resulting in a fully functional IoT communication and monitoring system that demonstrates the practical application of MQTT for both mobile app integration and system monitoring.

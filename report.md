# Laboratory Work: EXPO and MQTT Integration

## Aim of the Work
To integrate the provided EXPO application with an MQTT server and connect a backend subscriber that listens to messages from the EXPO mobile app.

## Environment Setup

For this lab, I opted to use Distrobox instead of VirtualBox as it provided a more lightweight containerization approach while maintaining full compatibility with the requirements.

### Container Creation

I created an Ubuntu 22.04 container using Distrobox:

```bash
distrobox create --name mqtt-ubuntu --image ubuntu:22.04
distrobox enter mqtt-ubuntu
```

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
tcp        0      0 0.0.0.0:1883            0.0.0.0:*               LISTEN      2132/mosquitto      
tcp6       0      0 :::8000                 :::*                    LISTEN      2132/mosquitto      
tcp6       0      0 :::1883                 :::*                    LISTEN      2132/mosquitto
```

I identified my IP address using:

```bash
ip r
```

Which returned my IP as `192.168.1.105` on the network `192.168.1.0/24`.

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
  '192.168.1.105',  // Updated to my IP address
  8000,           // Using WebSocket port
  `expo-mqtt-${Math.random().toString(16).substr(2, 8)}`
);
```

### Running the EXPO Application

I started the EXPO application with:

```bash
npx expo start
```

The application successfully launched and displayed a QR code that could be scanned with the Expo Go app. The logs confirmed connection to the MQTT broker:

```
 (NOBRIDGE) LOG  Connected to MQTT broker
 (NOBRIDGE) LOG  Subscribing to expo/test
 (NOBRIDGE) LOG  Subscribing to expo/result
 (NOBRIDGE) LOG  Subscribing to expo/status
```

## Python Backend Integration

### Setting Up Dependencies

I installed the required Python packages:

```bash
pip install paho-mqtt requests beautifulsoup4 lxml
```

### Configuring the MQTT Subscriber

I modified the provided `mqtt_sub.py` file to connect to my MQTT broker:

```python
# Configuration
MQTT_TOPIC = "expo/test"
MQTT_BROKER = "192.168.41.155"  # My broker's IP address
MQTT_PORT = 1883  # Standard MQTT port
```

### AliExpress Search Implementation

I developed a robust AliExpress search functionality to provide product information to the mobile app. The implementation in `aliexpress.py` utilizes multiple techniques to handle AliExpress's dynamic website structure:

#### 1. Multi-layered Search Approach

The search process follows these sequential steps:
1. Format and encode the search query for URL compatibility
2. Construct the AliExpress search URL and open it in a browser
3. Make an HTTP request to fetch the search results page
4. Process the page content using multiple extraction methods
5. Return structured product data or fallback to basic information

```python
def aliexpress_search(query):
    print(f"Searching AliExpress for: {query}")
    start_time = time.time()
    
    try:
        # Format query for URL
        formatted_query = quote_plus(query)
        
        # AliExpress search URL
        search_url = f"https://www.aliexpress.com/wholesale?SearchText={formatted_query}"
        
        # Open the search URL in browser
        webbrowser.open(search_url)
        print(f"Opening AliExpress search URL: {search_url}")
        
        # Rest of implementation...
```

#### 2. Product Data Extraction Strategies

The implementation uses three different strategies to extract product information:

1. **JSON Data Extraction**: Looks for embedded JSON data within script tags that contains structured product information
   ```python
   # Try to find product data in JSON format
   json_data = extract_json_data(soup)
   if json_data:
       return json_data
   ```

2. **Direct HTML Parsing**: When JSON data isn't available, it parses the HTML structure directly using various selectors that adapt to AliExpress's changing layout
   ```python
   # If no JSON data, try direct HTML parsing
   html_data = extract_html_data(soup, query, search_url)
   if html_data:
       return html_data
   ```

3. **Fallback Mechanism**: If both primary methods fail, it extracts basic product links to ensure some results are returned
   ```python
   # Try to find any elements with product info
   all_links = soup.find_all('a', href=True)
   product_links = [link for link in all_links if 'item/' in link.get('href', '')]
   ```

#### 3. Robust Error Handling

The implementation includes comprehensive error handling to ensure the search never crashes or hangs:

1. **Request Timeouts**: Prevents the search from hanging indefinitely
   ```python
   # Add a timeout to ensure the function doesn't hang indefinitely
   response = requests.get(search_url, headers=headers, timeout=10)
   ```

2. **Traceback Logging**: Detailed error information for debugging
   ```python
   except Exception as e:
       print(f"AliExpress search error: {e}")
       print(traceback.format_exc())  # Print full traceback for debugging
   ```

3. **Default Results**: Always returns at least basic search information even if extraction fails and tries to open link both on pc and mobile device
   ```python
   def basic_result(query, url):
       """Create a basic result when detailed extraction fails"""
       return {
           'query': str(query),
           'url_content': str(url),
           'products': [
               {
                   'title': f"Search results for {query}",
                   'price': "See website for prices",
                   'image': "",
                   'open_url': url,
                   'url': url
               }
           ]
       }
   ```

#### 4. Performance Monitoring

The implementation includes timing information to monitor search performance:
```python
elapsed = time.time() - start_time
print(f"Search completed in {elapsed:.2f} seconds")
```

A test of the search functionality with the query "Saw" completed in 1.84 seconds and successfully extracted information for 5 products, demonstrating the efficiency and reliability of the implementation.

### Running the Backend

I started the Python backend with:

```bash
python mqtt_sub.py
```

The script confirmed successful connection:

```
Created MQTT client using V2 API
Connecting to MQTT broker at 192.168.1.105:1883...
Connected to MQTT broker at 192.168.1.105
Subscribed to topic: expo/test
```

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
   [2025-04-16 12:26:16] Received message on expo/test: open: Google.com
   Opening URL:  Google.com
   ```
2. **AliExpress Searches**: Messages with the format `ali:PRODUCT_NAME` triggered product searches, opening the relevant page and returning structured data:
   ```
    [2025-04-21 21:20:28] Received message on expo/test: ali:hook
    Searching AliExpress for: hook
    Searching AliExpress for: hook
    Opening AliExpress search URL: https://www.aliexpress.com/wholesale?SearchText=hook
    Detected locale "C" with character encoding "ANSI_X3.4-1968", which is not UTF-8.
    Qt depends on a UTF-8 locale, and has switched to "C.UTF-8" instead.
    If this causes problems, reconfigure your locale. See the locale(1) manual
    for more information.
    No product cards found with main selectors, trying fallback selectors
    Found 22 product links as fallback
    Successfully extracted 5 products
    Search completed in 2.12 seconds
    Total search time: 2.12 seconds
    AliExpress results published to expo/result

   ```

3. **Regular Messages**: Any other text was logged with a timestamp and echoed back to confirm receipt.

### 3. Working Code Demonstration

The enhanced code successfully handles:

- **Connection Reliability**: Automatic reconnection if the connection is lost
- **Message Processing**: Parsing different message formats and executing appropriate actions
- **Data Extraction**: Reliable product data extraction from AliExpress using multiple methods
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
6. Understanding the key differences between MQTT protocols

The implementation shows how MQTT can be effectively used as a lightweight communication protocol for IoT and mobile applications, enabling real-time, asynchronous messaging between different platforms and technologies.

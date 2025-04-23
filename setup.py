#!/usr/bin/env python3
import os
import subprocess
import time
import threading
import json
import sys
import importlib.util

# Function to check if a package is installed
def is_package_installed(package_name):
    """Check if a Python package is installed"""
    return importlib.util.find_spec(package_name) is not None

# Function to install required packages
def ensure_required_packages():
    """Check and install required Python packages"""
    required_packages = ["paho-mqtt"]
    missing_packages = [pkg for pkg in required_packages if not is_package_installed(pkg.replace("-", "."))]
    
    if missing_packages:
        log_message(f"Missing required Python packages: {', '.join(missing_packages)}", "WARNING")
        try:
            log_message("Attempting to install missing packages...")
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages, check=True)
            log_message("Packages installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print("\n===== ERROR: Package Installation Failed =====")
            print(f"Failed to install required packages: {e}")
            print("\nPlease manually install the missing packages with:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
    return True

# Function for logging formatted messages
def log_message(message, level="INFO"):
    """Log formatted messages"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

# Try to import paho.mqtt.client - do this after defining helper functions
try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("\n===== ERROR: Required Package Missing =====")
    print("The paho-mqtt package is required but not installed.")
    print("\nTo fix this, run:")
    print("pip install paho-mqtt")
    print("\nIf you're using a virtual environment, activate it first with:")
    print("source venv/bin/activate")
    sys.exit(1)

import signal

# MQTT Configuration
MQTT_TOPIC_COMMAND = "expo/command"  # Topic for system commands
MQTT_TOPIC_RESPONSE = "expo/response"  # Topic for system responses
MQTT_TOPIC_STATUS = "expo/status"  # Topic for status updates
MQTT_PORT = 1883  # Standard MQTT port

# Container and app paths
CONTAINER_NAME = "mqtt-lab"
MQTT_APP_PATH = "/home/mark/Documents/mqtt-app"

def launch_container():
    """Launch the Distrobox container with Mosquitto broker"""
    log_message("Starting Mosquitto broker container setup")
    
    # Check if container exists
    result = subprocess.run(["distrobox", "list"], capture_output=True, text=True)
    
    if CONTAINER_NAME in result.stdout:
        log_message(f"Container '{CONTAINER_NAME}' exists, starting it")
        subprocess.run(["distrobox", "enter", CONTAINER_NAME, "--", 
                        "sudo", "systemctl", "start", "mosquitto"])
    else:
        log_message(f"Creating container '{CONTAINER_NAME}'")
        # Use the command from the lab instructions
        subprocess.run([
            "distrobox", "create", "--name", CONTAINER_NAME, 
            "--image", "ubuntu:22.04", 
            "--init", 
            "--additional-packages", "systemd systemd-sysv"
        ])
        
        log_message("Installing and configuring Mosquitto")
        # Setup commands exactly as in the lab
        commands = [
            "sudo apt update && sudo apt upgrade -y",
            "sudo apt install mosquitto mosquitto-clients vim net-tools -y",
            "sudo systemctl enable mosquitto",
            "sudo systemctl start mosquitto",
            # Write Mosquitto config
            """echo '# Place your local configuration in /etc/mosquitto/conf.d/
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
include_dir /etc/mosquitto/conf.d' | sudo tee /etc/mosquitto/mosquitto.conf""",
            "sudo systemctl restart mosquitto"
        ]
        
        for cmd in commands:
            subprocess.run(["distrobox", "enter", CONTAINER_NAME, "--", "bash", "-c", cmd])
    
    # Verify setup and get IP
    ip_result = subprocess.run(
        ["distrobox", "enter", CONTAINER_NAME, "--", "hostname", "-I"], 
        capture_output=True, text=True
    )
    broker_ip = ip_result.stdout.strip().split()[0]
    log_message(f"Mosquitto broker running at {broker_ip}")
    
    # Verify Mosquitto is listening
    subprocess.run(["distrobox", "enter", CONTAINER_NAME, "--", 
                    "bash", "-c", "sudo netstat -tulnp | grep mosquitto"])
    
    return broker_ip

def launch_expo_app():
    """Launch the EXPO application in a separate thread"""
    log_message("Starting EXPO application")
    
    def run_expo():
        os.chdir(MQTT_APP_PATH)
        try:
            # Install dependencies first
            subprocess.run(["npm", "install"], check=True)
            # Start the EXPO app
            subprocess.run(["npx", "expo", "start"], check=True)
        except Exception as e:
            log_message(f"Error launching EXPO app: {e}", "ERROR")
    
    # Start in background thread
    expo_thread = threading.Thread(target=run_expo)
    expo_thread.daemon = True
    expo_thread.start()
    
    # Wait for app to initialize
    time.sleep(3)
    log_message("EXPO app started in background")
    return expo_thread

def launch_mqtt_subscriber(broker_ip):
    """Launch the MQTT subscriber application in a separate thread"""
    log_message("Starting MQTT subscriber script")
    
    subscriber_script = os.path.join(MQTT_APP_PATH, "mqtt_sub.py")
    if not os.path.exists(subscriber_script):
        log_message(f"MQTT subscriber script not found at {subscriber_script}", "ERROR")
        return None
    
    def run_subscriber():
        try:
            # Use environment variable to pass the broker IP to the script
            env = os.environ.copy()
            env["MQTT_BROKER"] = broker_ip
            
            # Run the script with the broker IP as an argument
            subprocess.run([
                sys.executable, 
                subscriber_script, 
                "--broker", 
                broker_ip
            ], check=True, env=env)
        except Exception as e:
            log_message(f"Error launching MQTT subscriber: {e}", "ERROR")
    
    # Start in background thread
    subscriber_thread = threading.Thread(target=run_subscriber)
    subscriber_thread.daemon = True
    subscriber_thread.start()
    
    # Wait for script to initialize
    time.sleep(2)
    log_message("MQTT subscriber started in background")
    return subscriber_thread

def display_system_info():
    """Display system information"""
    print("\n===== System Information =====")
    
    # Get memory info
    mem_info = get_memory_info()
    if mem_info["status"] == "success":
        memory = mem_info["memory"]
        print(f"Memory: {memory['used']}MB used / {memory['total']}MB total ({memory['percent_used']}%)")
        print(f"Free memory: {memory['free']}MB, Available: {memory['available']}MB")
    
    # Get IP info
    ip_info = get_system_ip()
    if (ip_info["status"] == "success"):
        print("\nNetwork Interfaces:")
        if "interfaces" in ip_info:
            for iface, addrs in ip_info["interfaces"].items():
                print(f"  {iface}:")
                for addr in addrs:
                    print(f"    {addr['family']}: {addr['address']}")
        elif "raw_output" in ip_info:
            print("  IP information available (see raw output for details)")
    
    print("\n=============================")

# System command handlers
def list_directory():
    """Get contents of current directory"""
    try:
        files = os.listdir(".")
        return {
            "status": "success",
            "current_dir": os.getcwd(),
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_system_ip():
    """Get IP addresses of the system"""
    try:
        # Use ip addr command which works on most Linux systems
        result = subprocess.run(["ip", "-j", "addr"], capture_output=True, text=True)
        
        if result.returncode != 0:
            # Fallback to non-JSON version if -j isn't supported
            ip_result = subprocess.run(["ip", "addr"], capture_output=True, text=True)
            return {
                "status": "success",
                "raw_output": ip_result.stdout,
                "note": "Output provided as raw text, parser not implemented"
            }
        
        # Parse JSON output from ip -j addr
        interfaces = json.loads(result.stdout)
        ip_info = {}
        
        for interface in interfaces:
            name = interface.get("ifname", "unknown")
            ip_list = []
            
            for addr_info in interface.get("addr_info", []):
                if "local" in addr_info:
                    ip_list.append({
                        "address": addr_info["local"],
                        "family": "IPv4" if addr_info["family"] == "inet" else "IPv6"
                    })
            
            if ip_list:
                ip_info[name] = ip_list
                
        return {
            "status": "success",
            "interfaces": ip_info
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_memory_info():
    """Get free memory of the system"""
    try:
        # Use free command for memory information
        result = subprocess.run(["free", "-m"], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        
        # Parse the output
        headers = lines[0].split()
        mem_values = lines[1].split()
        
        memory = {
            "total": int(mem_values[1]),
            "used": int(mem_values[2]),
            "free": int(mem_values[3]),
            "shared": int(mem_values[4]),
            "buff_cache": int(mem_values[5]),
            "available": int(mem_values[6]),
            "unit": "MB"
        }
        
        # Calculate percentage used
        memory["percent_used"] = round((memory["used"] / memory["total"]) * 100, 2)
        
        return {
            "status": "success",
            "memory": memory
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def create_file(filename, content):
    """Create a new file with specified content"""
    try:
        # Basic security check
        if os.path.sep in filename or filename.startswith('.'):
            return {
                "status": "error", 
                "message": "Invalid filename. Cannot contain path separators or start with '.'"
            }
        
        with open(filename, 'w') as f:
            f.write(content)
        
        file_stats = os.stat(filename)
        
        return {
            "status": "success",
            "filename": filename,
            "full_path": os.path.abspath(filename),
            "size_bytes": file_stats.st_size,
            "created": time.ctime(file_stats.st_ctime)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# MQTT client callbacks
def on_connect(client, userdata, flags, rc, properties=None):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        log_message("Connected to MQTT broker successfully")
        client.subscribe(MQTT_TOPIC_COMMAND)
        log_message(f"Subscribed to {MQTT_TOPIC_COMMAND}")
        client.publish(MQTT_TOPIC_STATUS, "System monitor connected and ready")
    else:
        error_codes = {
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorized"
        }
        error_msg = error_codes.get(rc, f"Unknown error code: {rc}")
        log_message(f"Connection failed: {error_msg}", "ERROR")

def on_message(client, userdata, message):
    """Handle incoming MQTT messages"""
    msg_content = message.payload.decode('utf-8')
    log_message(f"Received message on {message.topic}: {msg_content}")
    
    if message.topic != MQTT_TOPIC_COMMAND:
        return
    
    try:
        response = {
            "command": msg_content,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Process commands
        if msg_content == "list_directory":
            response.update(list_directory())
        
        elif msg_content == "get_ip":
            response.update(get_system_ip())
        
        elif msg_content == "get_memory":
            response.update(get_memory_info())
        
        elif msg_content.startswith("create_file:"):
            try:
                # Parse filename and content
                parts = msg_content[12:].split('|', 1)
                if len(parts) != 2:
                    response.update({
                        "status": "error",
                        "message": "Invalid format. Use: create_file:filename|content"
                    })
                else:
                    filename, content = parts
                    response.update(create_file(filename, content))
            except Exception as e:
                response.update({
                    "status": "error",
                    "message": f"File creation failed: {str(e)}"
                })
        
        else:
            response.update({
                "status": "error",
                "message": f"Unknown command: {msg_content}"
            })
        
        # Send response
        client.publish(MQTT_TOPIC_RESPONSE, json.dumps(response))
        log_message(f"Response sent to {MQTT_TOPIC_RESPONSE}")
        
    except Exception as e:
        error_msg = f"Error processing command: {str(e)}"
        log_message(error_msg, "ERROR")
        error_response = {
            "command": msg_content,
            "status": "error",
            "message": error_msg,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        client.publish(MQTT_TOPIC_RESPONSE, json.dumps(error_response))

def init_mqtt_client(broker_ip):
    """Initialize the MQTT client"""
    try:
        client = mqtt.Client(
            client_id="SystemMonitor", 
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
        log_message("Created MQTT client with V2 API")
    except (AttributeError, ValueError):
        # Fallback for older versions
        client = mqtt.Client("SystemMonitor")
        log_message("Created MQTT client with V1 API")
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Set last will message
    client.will_set(
        MQTT_TOPIC_STATUS, 
        "System monitor disconnected unexpectedly", 
        qos=1, 
        retain=False
    )
    
    # Connect to broker
    log_message(f"Connecting to MQTT broker at {broker_ip}:{MQTT_PORT}")
    client.connect(broker_ip, MQTT_PORT, 60)
    client.loop_start()
    
    return client

def main():
    """Main function"""
    print("\n===== MQTT System Monitor Setup =====\n")
    
    # Ensure required packages are installed
    if not ensure_required_packages():
        log_message("Missing required packages. Please install them and try again.", "ERROR")
        return 1
    
    # Display system info at startup
    display_system_info()
    
    # Launch container with Mosquitto broker
    broker_ip = launch_container()
    if not broker_ip:
        log_message("Failed to set up broker container", "ERROR")
        return 1
        
    # Launch EXPO app
    expo_thread = launch_expo_app()
    
    # Launch MQTT subscriber
    subscriber_thread = launch_mqtt_subscriber(broker_ip)
    
    # Initialize MQTT client for system commands
    client = init_mqtt_client(broker_ip)
    if not client:
        log_message("Failed to initialize MQTT client", "ERROR")
        return 1
    
    # Display available commands
    print("\n===== System Monitor Ready =====")
    print(f"Listening for commands on topic: {MQTT_TOPIC_COMMAND}")
    print(f"Broker IP: {broker_ip}")
    print("\nAvailable commands:")
    print("  list_directory - List contents of current directory")
    print("  get_ip - Show system IP addresses")
    print("  get_memory - Show system memory information")
    print("  create_file:filename|content - Create a new file")
    print("\nPress Ctrl+C to exit\n")
    
    # Keep running until keyboard interrupt
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        client.publish(MQTT_TOPIC_STATUS, "System monitor shutting down")
        client.loop_stop()
        client.disconnect()
        print("Cleanup complete. Exiting.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
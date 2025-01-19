import pigpio
import socket
import time
import random
import threading

# Configuration
ir_rx_pin = 16  # GPIO 16 for IR receiver
receiver_ip = '192.168.137.1'  # Main computer IP address
port = 12345  # Port for communication with the main computer
sender_pi_ip = '192.168.137.73'  # IP of the sender Raspberry Pi
server_port = 12346  # Port for communication with the sender Raspberry Pi
timeout = 1  # Timeout in seconds for IR heartbeat

# GPIO configuration for LED
led_pin = 4  # GPIO 4 for LED

# Initialize pigpio library
pi = pigpio.pi()
if not pi.connected:
    print("Failed to connect to pigpio daemon.")
    exit()

# Set up LED pin
pi.set_mode(led_pin, pigpio.OUTPUT)
pi.write(led_pin, 0)  # Make sure the LED is off initially

# IR Receiver setup
pi.set_mode(ir_rx_pin, pigpio.INPUT)

# Global flag to track LED state
led_active = False
led_duration = 0

# Track the start time for uptime calculation
start_time = time.time()

# Function to calculate uptime
def get_uptime():
    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Function to check if a heartbeat has been received
def check_for_heartbeat():
    heartbeat_received = False

    def ir_callback(gpio, level, tick):
        nonlocal heartbeat_received
        if level == 1:  # IR signal detected
            heartbeat_received = True

    callback = pi.callback(ir_rx_pin, pigpio.EITHER_EDGE, ir_callback)
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(0.1)
        if heartbeat_received:
            break
    callback.cancel()
    return heartbeat_received

# Function to send data to the main computer
def send_data_to_computer(raspberry_pi_id, client_socket,hearbeat_received):
    try:
        soil_humidity = random.uniform(0, 100)
        water_level = random.uniform(0, 100)
        temperature = random.uniform(0, 100)
        fertilizer_level = random.uniform(0, 100)
        hearbeat_received = hearbeat_received

        uptime = get_uptime()  # Get the uptime of the system
        message = f"{raspberry_pi_id},{soil_humidity},{water_level},{temperature},{fertilizer_level},{uptime},{hearbeat_received}"
        client_socket.sendall(message.encode())
        print(f"Sent to computer: {message}")
    except Exception as e:
        print(f"Error: {e}")

# Function to send data to the sender Raspberry Pi if no heartbeat is received
def notify_sender_pi(data):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((sender_pi_ip, server_port))
        print(f"Connected to {sender_pi_ip}:{server_port}")
        client_socket.sendall(data.encode())
        print(f"Sent to sender Pi: {data}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

# Establish persistent connection to the main computer
def establish_connection_to_computer():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((receiver_ip, port))
        print(f"Connected to {receiver_ip}:{port}")
        return client_socket
    except Exception as e:
        print(f"Error establishing connection to computer: {e}")
        return None

# Function to listen for LED control command from the computer
def listen_for_led_command():
    global led_active, led_duration
    led_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    led_socket.bind(('0.0.0.0', 12347))  # Listen on all interfaces on port 12347
    led_socket.listen(1)  # Only accept one connection
    print("Listening for LED control command on port 12347...")

    while True:
        client, address = led_socket.accept()
        print(f"Connection from {address}")

        try:
            command = client.recv(1024).decode()
            print(f"Received command: {command}")

            # Check if the command is to turn on the LED with a duration
            if command.startswith("TURN_ON_LED"):
                try:
                    # Extract the duration from the command
                    _, duration_str = command.split(",")
                    duration = float(duration_str.strip())
                    print(f"Turning on LED for {duration} seconds...")
                    
                    # Set global flags for LED
                    led_active = True
                    led_duration = duration
                    pi.write(led_pin, 1)  # Turn on LED
                    print(f"LED turned on for {duration} seconds.")
                    
                    # Start a separate thread to turn off LED after duration
                    threading.Thread(target=turn_off_led_after_duration).start()

                except ValueError:
                    print("Invalid duration value received.")
            elif command == "TURN_OFF_LED":
                print("Turning off LED immediately.")
                led_active = False
                pi.write(led_pin, 0)  # Turn off LED immediately
            else:
                print("Invalid command received.")
        except Exception as e:
            print(f"Error receiving command: {e}")
        finally:
            client.close()

# Function to turn off LED after the specified duration
def turn_off_led_after_duration():
    global led_active, led_duration
    time.sleep(led_duration)
    if led_active:
        print(f"LED turned off after {led_duration} seconds.")
        pi.write(led_pin, 0)  # Turn off LED
        led_active = False

# Main loop
client_socket = establish_connection_to_computer()
if client_socket:
    # Start the LED listener in a separate thread
    led_thread = threading.Thread(target=listen_for_led_command)
    led_thread.daemon = True
    led_thread.start()

    while True:
        print("Checking for heartbeat...")
        if not check_for_heartbeat():
            print("No heartbeat received. Sending data to the main computer...")
            print("Notifying sender Pi about no heartbeat...")
            notify_sender_pi("No heartbeat detected. Receiver is sending data.")
            send_data_to_computer("pi_1", client_socket,False)

        else:
            print("Heartbeat received. Sending data to the main computer...")
            send_data_to_computer("pi_1", client_socket,True)


        time.sleep(2)
else:
    print("Unable to establish connection to the main computer.")

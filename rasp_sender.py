import random 
import pigpio
import socket
import time
import threading

# Configuration
ir_tx_pin = 5  # GPIO 5 for IR transmitter
led_pin = 4     # GPIO 4 for LED (same as the first Raspberry Pi)
receiver_ip = '192.168.137.1'  # Main computer IP address
port = 12344  # Port for communication with the main computer
server_port = 12346  # Port for communication with the receiver Raspberry Pi

# Initialize pigpio library
pi = pigpio.pi()
if not pi.connected:
    print("Failed to connect to pigpio daemon.")
    exit()

# IR Transmitter setup
pi.set_mode(ir_tx_pin, pigpio.OUTPUT)

# Set up LED pin
pi.set_mode(led_pin, pigpio.OUTPUT)
pi.write(led_pin, 0)  # Make sure the LED is off initially

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

# Function to send heartbeat via IR
def send_heartbeat():
    pi.write(ir_tx_pin, 1)
    time.sleep(0.1)
    pi.write(ir_tx_pin, 0)

# Function to send data to the main computer
def send_data_to_computer(raspberry_pi_id, client_socket):
    try:
        soil_humidity = random.uniform(0, 100)
        water_level = random.uniform(0, 100)
        temperature = random.uniform(0, 100)
        fertilizer_level = random.uniform(0, 100)
        uptime = get_uptime()  # Get the uptime of the system
        message = f"{raspberry_pi_id},{soil_humidity},{water_level},{temperature},{fertilizer_level},{uptime}"
        client_socket.sendall(message.encode())
        print(f"Sent to computer: {message}")
    except Exception as e:
        print(f"Error: {e}")

# Function to handle incoming data from the receiver Raspberry Pi
def receive_data_from_receiver_pi():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', server_port))
    server_socket.listen(1)
    print(f"Listening on port {server_port} for data from the receiver Pi...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        data = client_socket.recv(1024).decode()
        if data:
            print(f"Received data from receiver Pi: {data}")
        client_socket.close()

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

# Start a thread to listen for incoming data from the receiver Raspberry Pi
server_thread = threading.Thread(target=receive_data_from_receiver_pi)
server_thread.daemon = True
server_thread.start()

# Start a thread to listen for LED control commands
led_thread = threading.Thread(target=listen_for_led_command)
led_thread.daemon = True
led_thread.start()

# Main loop
client_socket = establish_connection_to_computer()

while True:
    print("Sending heartbeat...")
    send_heartbeat()
    print("Sending data to main computer...")
    send_data_to_computer("pi_2", client_socket)
    time.sleep(2)

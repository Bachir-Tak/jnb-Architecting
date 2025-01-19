import tkinter as tk
import tk_tools
import socket
import threading
import time

class MonitoringApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Interface de Surveillance")

        self.root.resizable(False, False)  # Disable resizing
        
        # Variables pour stocker les jauges et les indicateurs
        self.gauges = {}
        self.sensor_values = {}  # Dictionnaire pour stocker les valeurs des capteurs
        self.pump_states = {}  # Dictionnaire pour les états des pompes
        self.pump_activation_times = {}  # Temps d'activation des pompes
        self.sliders = {}
        self.client_socket = None  # Socket pour envoyer les commandes
        self.led_status={}
        self.heartbeat_received = True

        # Ajouter les sections de monitoring et le type de communication
        self.create_monitoring_section("Monitoring Field 1", 0, 0,"192.168.137.21")
        self.add_communication_line(0, 1)
        self.create_monitoring_section("Monitoring Field 2", 0, 2,"192.168.137.73")

        # Start the socket listener in a separate thread to receive data
        self.receive_thread_1 = threading.Thread(target=self.receive_data, args=("pi_1", 12345))
        self.receive_thread_1.daemon = True
        self.receive_thread_1.start()

        self.receive_thread_2 = threading.Thread(target=self.receive_data, args=("pi_2", 12344))
        self.receive_thread_2.daemon = True
        self.receive_thread_2.start()
        self.led_status[f"Monitoring Field 1"]="OFF"
        self.led_status[f"Monitoring Field 2"]="OFF"



    def create_monitoring_section(self, title, row, col,raspberry_ip):
        frame = tk.LabelFrame(self.root, text=title, padx=10, pady=10)
        frame.grid(row=row, column=col, padx=20, pady=20, sticky="n")

        # Ajouter les jauges et les indicateurs
        self.add_gauges_and_indicator(frame, title,raspberry_ip)

    def add_gauges_and_indicator(self, frame, title,raspberry_ip):
        # Créer une sous-frame pour les jauges
        gauges_frame = tk.Frame(frame)
        gauges_frame.grid(row=0, column=0, padx=10, pady=10)

        # Ajouter les jauges en grille 2x2
        self.add_gauge(gauges_frame, f"{title} - Soil humidity", 0, 0)
        self.add_gauge(gauges_frame, f"{title} - Water level", 0, 1)
        self.add_gauge(gauges_frame, f"{title} - Temperature", 1, 0)
        self.add_gauge(gauges_frame, f"{title} - Fertilizer level", 1, 1)

        # Créer une sous-frame pour l'indicateur de pompe
        indicator_frame = tk.Frame(frame)
        indicator_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")

        pump_label = tk.Label(indicator_frame, text="Pump: OFF", fg="red", font=("Arial", 12))
        pump_label.pack(pady=5)

        pump_time_label = tk.Label(indicator_frame, text="Time: 0s", font=("Arial", 10))
        pump_time_label.pack(pady=5)

        # Enregistrer les indicateurs
        self.pump_states[title] = pump_label
        self.pump_activation_times[title] = {"label": pump_time_label, "time": 0, "active": False}

        # Ajouter la section de personnalisation en dessous
        self.add_parameter_customization(frame, title, raspberry_ip)

    def add_gauge(self, frame, label, row, col):
        # Ajouter une légende au-dessus de la jauge
        tk.Label(frame, text=label.split(" - ")[1], font=("Arial", 10)).grid(row=row * 2, column=col, pady=5)

        # Créer une jauge rotative
        gauge = tk_tools.RotaryScale(frame, max_value=100.0, unit="", size=100)
        gauge.grid(row=row * 2 + 1, column=col, padx=20, pady=10)

        # Enregistrer la jauge pour mise à jour ultérieure
        self.gauges[label] = gauge

        # Ajouter l'étiquette au dictionnaire des valeurs avec une valeur par défaut
        self.sensor_values[label] = 0.0

    def add_parameter_customization(self, frame, title,raspberry_ip):
        # Ajouter une section de personnalisation
        customization_frame = tk.Frame(frame, bg="lightgray", padx=10, pady=10)
        customization_frame.grid(row=1, column=0, columnspan=2, pady=10)

        # Titre
        tk.Label(customization_frame, text="Parameter personalisation for alerting", font=("Arial", 10, "bold"), bg="lightgray").grid(row=0, column=0, columnspan=4, pady=5)

        # Curseurs pour les paramètres
        slider_labels = ["Water level", "Temperature", "Soil humidity", "Fertilizer level"]
        for i, slider_label in enumerate(slider_labels):
            tk.Label(customization_frame, text=slider_label, font=("Arial", 10), bg="lightgray").grid(row=1, column=i, padx=5)
            slider = tk.Scale(customization_frame, from_=0, to=100, orient="vertical", bg="lightgray")
            slider.set(100)  # Set the default value to 100

            slider.grid(row=2, column=i, padx=5)
            self.sliders[f"{title} - {slider_label}"] = slider

        # Indicateurs pour "Active pump"
        tk.Label(customization_frame, text="Activate pump", font=("Arial", 10), bg="lightgray").grid(row=3, column=0, padx=5, columnspan=2)

        def toggle_switch():
            current_state = pump_switch.cget("text")
            activation_time_value = activation_time.get()  # Get the value from the entry field

            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((raspberry_ip, 12347))  # Raspberry Pi IP and control port
            if current_state == "OFF":
                pump_switch.config(text="ON", bg="green")
                # Send command to turn on LED for the pump (with example duration)
                self.send_led_command(f"TURN_ON_LED, {activation_time_value}")  # Turn on LED for 5 seconds
                self.led_status[f"{title}"]="ON"
            else:
                pump_switch.config(text="OFF", bg="red")
                # Send command to turn off the LED
                self.send_led_command("TURN_OFF_LED")
                self.led_status[f"{title}"]="OFF"


        pump_switch = tk.Button(customization_frame, text="OFF", bg="red", width=6, command=toggle_switch)
        pump_switch.grid(row=4, column=0, padx=5, columnspan=2)

        tk.Label(customization_frame, text="Time of activation", font=("Arial", 10), bg="lightgray").grid(row=3, column=2, padx=5, columnspan=2)
        activation_time = tk.Entry(customization_frame, width=10)
        activation_time.insert(0, "1")  # Default value inserted
        activation_time.grid(row=4, column=2, padx=5, columnspan=2)
        
        self.activation_time = activation_time  # Store the reference to the entry field


    def send_led_command(self, command):
        if self.client_socket:
            try:
                self.client_socket.sendall(command.encode())  # Send command to the Raspberry Pi
                print(f"Command sent: {command}")
            except Exception as e:
                print(f"Error sending command: {e}")

    def add_communication_line(self, row, col):
        frame = tk.Frame(self.root, width=800, height=50)  # Fixed width of 400px for the communication line
        frame.grid(row=row, column=col, padx=10, pady=1, sticky="n")

        tk.Label(frame, text="Communication type/state", font=("Arial", 12, "bold"), anchor="center",width=50).pack()
        tk.Canvas(frame, height=5, width=200, bg="blue").pack(pady=10)

        # Create a canvas to hold the messages
        self.canvas = tk.Canvas(frame)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Create a scrollbar for the canvas
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Create a frame inside the canvas to hold the labels
        self.message_frame = tk.Frame(self.canvas)
        self.canvas.create_window((100, 0), window=self.message_frame, anchor="nw")

        # Configure the canvas scroll region
        self.message_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
         # Create another frame with the label "IR Comm: Established"
        self.ir_comm_frame = tk.Frame(self.root, width=800, height=30)
        self.ir_comm_frame.grid(row=row + 1, column=col, padx=10, pady=1, sticky="n")

        self.ir_comm_label = tk.Label(self.ir_comm_frame, text="IR Comm : Established", font=("Arial", 12, "bold"), fg="green", anchor="center", width=50)
        self.ir_comm_label.pack()
        
    def update_communication_line(self, message):
        # Get the communication frame
        label = tk.Label(self.message_frame, text=message, font=("Arial", 10), fg="red", anchor="w", width=50, wraplength=380)  # Added bd=1 and relief="solid" for a border around each message label
        label.pack(anchor="w", pady=2) 
        self.canvas.yview_moveto(1)  # Scroll to the bottom of the canvas (1 means 100% scrolled to the bottom)

    
        
    def update_sensor_values(self,monitor_number,uptime):
        # Mettre à jour les valeurs des capteurs et les indicateurs
        for label in self.sensor_values.keys():
            self.gauges[label].set_value(self.sensor_values[label])
            # Identifier le champ de monitoring correspondant
            field_title = label.split(" - ")[0]
            
                        # Check if any sensor value exceeds 50 and update communication line
            if self.sensor_values[label] > self.sliders[label].get():
                self.update_communication_line(f"{label.split(' - ')[1]} of Field {monitor_number} exceeds the limit : {self.sensor_values[label]} > {self.sliders[label].get()}, should be investigated. (at {uptime})")

            # Gestion de l'état de la pompe (actif si la valeur > 70)
            pump_active = self.sensor_values[label] > 70
            pump_label = self.pump_states[field_title]
            pump_time_info = self.pump_activation_times[f"Monitoring Field {monitor_number}"]


            if self.led_status[f"{field_title}"]=="ON":
                pump_label.config(text="Pump: ON", fg="green")
            elif pump_active:
                pump_label.config(text="Pump: ON", fg="green")
                if not pump_time_info["active"]:
                    pump_time_info["active"] = True
            else:
                pump_label.config(text="Pump: OFF", fg="red")
                if pump_time_info["active"]:
                    pump_time_info["active"] = False
            pump_time_info["label"].config(text=f"Time: {uptime}s")
            
        if self.heartbeat_received==True:
            self.ir_comm_label.config(text="IR Comm : Established", fg="green")
        else:
            self.ir_comm_label.config(text="IR Comm : Lost", fg="red")

        # Planifier la prochaine mise à jour après 1 seconde
        self.root.after(1000, self.update_sensor_values)

    def receive_data(self, raspberry_id, port):
        # Set up a socket to receive data from Raspberry Pi
        server_ip = '0.0.0.0'  # Listen on all available network interfaces
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((server_ip, port))
        server_socket.listen(1)

        print(f"Waiting for connection from {raspberry_id}...")
        conn, addr = server_socket.accept()
        print(f"Connection established with {addr} for {raspberry_id}")

        while True:
            try:
                # Receive data from Raspberry Pi
                data = conn.recv(1024).decode()
                if data:
                    # Parse the sensor data (CSV format)
                    sensor_data = data.split(',')
                    raspberry_number = sensor_data.pop(0)

                    # Determine the monitoring field based on the Raspberry Pi
                    monitor_number = 1 if raspberry_number == "pi_1" else 2
                    print(data)

                    # Check if the received data contains 5 elements (sensor data + uptime)
                    if len(sensor_data) == 6:
                        # Extract sensor data and uptime
                        soil_humidity, water_level, temperature, fertilizer_level, uptime,heartbeat_received = sensor_data

                        # Parse sensor values into floats
                        soil_humidity = round(float(soil_humidity), 2)
                        water_level = round(float(water_level), 2)
                        temperature = round(float(temperature), 2)
                        fertilizer_level = round(float(fertilizer_level), 2)

                        # Update the sensor values for both fields
                        self.sensor_values[f"Monitoring Field {monitor_number} - Soil humidity"] = soil_humidity
                        self.sensor_values[f"Monitoring Field {monitor_number} - Water level"] = water_level
                        self.sensor_values[f"Monitoring Field {monitor_number} - Temperature"] = temperature
                        self.sensor_values[f"Monitoring Field {monitor_number} - Fertilizer level"] = fertilizer_level
                        self.heartbeat_received=str.lower(heartbeat_received) == "true"

                        # Update the UI with the new values
                        self.update_sensor_values(monitor_number,uptime)
                    elif len(sensor_data) == 5:
                        # Extract sensor data and uptime
                        soil_humidity, water_level, temperature, fertilizer_level, uptime = sensor_data

                        # Parse sensor values into floats
                        soil_humidity = round(float(soil_humidity), 2)
                        water_level = round(float(water_level), 2)
                        temperature = round(float(temperature), 2)
                        fertilizer_level = round(float(fertilizer_level), 2)

                        # Update the sensor values for both fields
                        self.sensor_values[f"Monitoring Field {monitor_number} - Soil humidity"] = soil_humidity
                        self.sensor_values[f"Monitoring Field {monitor_number} - Water level"] = water_level
                        self.sensor_values[f"Monitoring Field {monitor_number} - Temperature"] = temperature
                        self.sensor_values[f"Monitoring Field {monitor_number} - Fertilizer level"] = fertilizer_level

                        # Update the UI with the new values
                        self.update_sensor_values(monitor_number,uptime)
                    else:
                        print("Received invalid data format.")
            except Exception as e:
                print(f"Error receiving data: {e}")
                break

        conn.close()



# Lancement de l'application
root = tk.Tk()
app = MonitoringApp(root)
root.mainloop()


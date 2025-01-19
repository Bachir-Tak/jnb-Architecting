# Architecting IoT System Project

## Introduction

This project is part of the **Architecting IoT System** course. It demonstrates the connection between two Raspberry Pi devices exchanging data using **IR signals** or **WiFi**, and visualizing that data on a **digital twin** interface on the computer. The interface includes commands and alerts for interaction.
The project was made by **Julien Soto**, **Nicolas Zanin** and **Bachir Benna**.

---

## Setup Instructions

### If You Don’t Have the Same SD Cards as Us:

#### Step 1: Install a 64-bit OS on Both SD Cards

- During the configuration process, change the **SSID** and the **password** to the desired network.
- Ensure that the network hosts your computer and both Raspberry Pi devices.
  - **Tip**: Start a Wi-Fi hotspot on your computer to act as the network.

#### Step 2: Connect to Each Raspberry Pi

After installing the OS:

1. Connect to each Raspberry Pi using the following command:
   ```bash
   ssh pi@<ip_of_the_raspberry>
   ```
2. Clone the project repository:
   ```bash
   git clone https://github.com/Bachir-Tak/jnb-Architecting.git
   ```

#### Step 3: Install the Pigpio Library

Run the following command to install the pigpio library:

```bash
sudo apt install pigpio python3-pigpio -y
```

#### Step 4: Enable the Pigpiod Daemon

The pigpio library uses a daemon (`pigpiod`) to interface with GPIO. Enable and start the daemon with:

```bash
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

Check the status to ensure it’s running:

```bash
sudo systemctl status pigpiod
```

#### Step 5: Modify the Python Files

1. Update **`sender.py`**:
   - Set the IP address (line 10) to the IP of your computer.
2. Update **`receiver.py`**:
   - Set `receiver_ip` (line 9) to the IP of your computer.
   - Set `sender_pi_ip` (line 11) to the IP of the other Raspberry Pi.

#### Step 6: Connect Hardware

1. On the **receiver Raspberry Pi**:
   - Connect a **LED** to GPIO4.
   - Connect the **IR receiver** to pin D16.
2. On the **sender Raspberry Pi**:
   - Connect a **LED** to GPIO4.
   - Connect the **IR sender** to pin D5.

#### Step 7: Start the Application

1. Run **`app.py`** on your computer.
2. Run **`receiver.py`** on the receiver Raspberry Pi.
3. Run **`sender.py`** on the sender Raspberry Pi.

> **Note**: If no data is displayed on the `app.py` dashboard, try the following:
>
> - Deactivate your firewall.
> - Add an exception for the currently used network.

---

### If You Have the Same SD Cards and Setup as Us:

#### Step 1: Host an Access Point on Your Computer

Use the following credentials for the access point:

- **SSID**: `Zephm`
- **Password**: `billie2002`

#### Step 2: Boot the Raspberry Pi Devices

1. Verify that the IP addresses of the Raspberry Pi devices match those in the configuration files.
2. If they do not match, follow the "Modify the Python Files" section above.

#### Step 3: Start the Application

1. Run **`app.py`** on your computer.
2. Run **`receiver.py`** on the receiver Raspberry Pi.
3. Run **`sender.py`** on the sender Raspberry Pi.

> **Note**: If no data is displayed on the `app.py` dashboard, try the following:
>
> - Deactivate your firewall.
> - Add an exception for the currently used network.

---

We hope the project is to your liking !

---

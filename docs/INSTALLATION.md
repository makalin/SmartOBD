# SmartOBD Installation Guide

This guide will help you install and set up SmartOBD on your system.

## Prerequisites

- Python 3.8 or higher
- OBD-II adapter (Bluetooth, WiFi, or USB)
- Vehicle with OBD-II port (1996 or newer)

## Installation Options

### Option 1: Direct Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/techdrivex/SmartOBD.git
   cd SmartOBD
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install SmartOBD:**
   ```bash
   pip install -e .
   ```

### Option 2: Using Docker

1. **Build the Docker image:**
   ```bash
   docker build -t smartobd .
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

### Option 3: Using Make

1. **Run the setup:**
   ```bash
   make setup
   make install
   ```

## Configuration

1. **Copy the configuration template:**
   ```bash
   cp config.yaml config_local.yaml
   ```

2. **Edit the configuration:**
   ```bash
   nano config_local.yaml
   ```

3. **Configure your OBD-II connection:**
   - For Bluetooth: Set `connection_type: "bluetooth"`
   - For WiFi: Set `connection_type: "wifi"` and configure IP address
   - For USB: Set `connection_type: "usb"`

4. **Configure notifications (optional):**
   - Email: Set up SMTP credentials
   - SMS: Configure Twilio credentials
   - Push: Add Pushbullet API key

## Quick Start

### Basic Usage

1. **Start the application:**
   ```bash
   python smartobd.py
   ```

2. **Connect to OBD-II device:**
   ```bash
   python smartobd.py --connect
   ```

3. **Start monitoring:**
   ```bash
   python smartobd.py --monitor
   ```

4. **Open web dashboard:**
   ```bash
   python smartobd.py --dashboard
   ```
   Then open http://localhost:5000 in your browser.

### Interactive CLI

1. **Start interactive mode:**
   ```bash
   python smartobd.py
   ```

2. **Available commands:**
   ```
   SmartOBD> help
   SmartOBD> connect
   SmartOBD> start
   SmartOBD> dashboard
   SmartOBD> status
   SmartOBD> quit
   ```

## OBD-II Adapter Setup

### Bluetooth Adapters

1. **Pair your Bluetooth adapter:**
   ```bash
   bluetoothctl
   scan on
   pair <MAC_ADDRESS>
   trust <MAC_ADDRESS>
   connect <MAC_ADDRESS>
   ```

2. **Create RFCOMM device:**
   ```bash
   sudo rfcomm bind 0 <MAC_ADDRESS> 1
   ```

### WiFi Adapters

1. **Connect to adapter's WiFi network**
2. **Configure IP address in config.yaml:**
   ```yaml
   obd:
     connection_type: "wifi"
     # Default IP is usually 192.168.0.10:35000
   ```

### USB Adapters

1. **Connect USB adapter to OBD-II port**
2. **Check device permissions:**
   ```bash
   sudo chmod 666 /dev/ttyUSB0
   ```

## Troubleshooting

### Common Issues

1. **Permission denied on USB device:**
   ```bash
   sudo usermod -a -G dialout $USER
   # Log out and back in
   ```

2. **Bluetooth connection issues:**
   ```bash
   sudo systemctl start bluetooth
   sudo systemctl enable bluetooth
   ```

3. **Python dependencies issues:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

4. **Database connection issues:**
   ```bash
   # Check if SQLite is working
   python -c "import sqlite3; print('SQLite OK')"
   ```

### Logs

Check the logs for detailed error information:
```bash
tail -f logs/smartobd.log
```

### Testing

Run the test suite:
```bash
make test
```

## Development Setup

1. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8 mypy
   ```

2. **Run linting:**
   ```bash
   make lint
   ```

3. **Run tests:**
   ```bash
   make test
   ```

## Production Deployment

### Using Docker

1. **Build production image:**
   ```bash
   docker build -t smartobd:latest .
   ```

2. **Run with Docker Compose:**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

### Using Systemd

1. **Create service file:**
   ```bash
   sudo nano /etc/systemd/system/smartobd.service
   ```

2. **Add service configuration:**
   ```ini
   [Unit]
   Description=SmartOBD Vehicle Monitoring
   After=network.target

   [Service]
   Type=simple
   User=smartobd
   WorkingDirectory=/opt/smartobd
   ExecStart=/usr/bin/python3 smartobd.py --monitor
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service:**
   ```bash
   sudo systemctl enable smartobd
   sudo systemctl start smartobd
   ```

## Support

If you encounter issues:

1. Check the [FAQ](FAQ.md)
2. Review the [troubleshooting guide](TROUBLESHOOTING.md)
3. Open an issue on GitHub
4. Check the logs for error details

## License

SmartOBD is licensed under the MIT License. See [LICENSE](../LICENSE) for details. 
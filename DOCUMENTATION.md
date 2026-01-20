# MHP Raspicam V4 - Technical Documentation

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Configuration](#configuration)
6. [Development Guide](#development-guide)
7. [Deployment](#deployment)
8. [API Reference](#api-reference)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### Purpose

The MHP Raspicam V4 is a Raspberry Pi-based camera system designed for the Monash Human Power bike project. It overlays real-time telemetry data (power, cadence, speed, heart rate, etc.) onto a live camera feed and records video during bike testing sessions.

### Key Features

- **Real-time Telemetry Overlay**: Displays bike sensor data overlaid on camera feed
- **MQTT Integration**: Receives data from bike's Data Acquisition System (DAS)
- **Video Recording**: Records H.264 video to disk during logging sessions
- **Hardware Control**: Manages LEDs and switches for status indication and control
- **Multi-Backend Support**: Works on Raspberry Pi (PiCamera) and development machines (OpenCV)
- **Modular Overlay System**: Easy to create custom overlay layouts
- **Error Handling**: Graceful degradation with error reporting via MQTT

### Tech Stack

- **Language**: Python 3.7
- **Dependency Management**: Poetry
- **Video Processing**: OpenCV 4.x
- **Camera Interface**: PiCamera (Raspberry Pi only)
- **Communication**: MQTT (paho-mqtt)
- **Hardware Control**: RPi.GPIO, Adafruit CircuitPython MCP3xxx
- **Configuration**: JSON + environment variables (python-dotenv)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MQTT Broker                              │
│  (Receives telemetry from bike sensors, sends commands)    │
└────────────┬──────────────────────────────┬─────────────────┘
             │                              │
             │                              │
    ┌────────▼────────┐          ┌─────────▼─────────┐
    │  Orchestrator   │          │   Overlay Process  │
    │   (orchestrator)│          │   (overlay_*.py)   │
    │                 │          │                     │
    │ - MQTT client   │          │ - MQTT client      │
    │ - Status mgmt   │          │ - Data parsing     │
    │ - LED control   │          │ - Canvas rendering │
    │ - Battery mon.  │          │ - Video overlay    │
    └────────┬────────┘          └─────────┬──────────┘
             │                              │
             │                              │
    ┌────────▼──────────────────────────────▼─────────┐
    │         Hardware Abstraction Layer (HAL)       │
    │  - LEDs (display power, MQTT, logging status)  │
    │  - Switches (logging button, display power)   │
    │  - ADC (battery voltage monitoring)           │
    └────────────────────────────────────────────────┘
             │
    ┌────────▼────────┐
    │  Raspberry Pi   │
    │  Hardware       │
    └─────────────────┘
```

### Component Relationships

1. **Orchestrator** runs as a background service, managing MQTT connections and hardware status
2. **Switch Handler** monitors physical switch and starts/stops overlay processes
3. **Overlay Process** handles video capture, data display, and recording
4. **Hardware Layer** abstracts bike-specific hardware differences (V2 vs V3)

---

## Core Components

### 1. Orchestrator (`orchestrator.py`)

The orchestrator is the main control service that runs continuously on the Raspberry Pi.

#### Responsibilities

- **MQTT Connection Management**: Maintains connection to MQTT broker
- **Camera Status Publishing**: Reports camera online/offline status and IP address
- **Logging State Management**: Tracks and controls data logging state
- **Overlay Control**: Receives commands to switch overlays remotely
- **Battery Monitoring**: Periodically publishes battery voltage
- **Hardware LED Control**: Updates LEDs based on system state

#### Key Methods

```python
class Orchestrator:
    def toggle_logging(self, _) -> None:
        """Toggles logging state when physical button is pressed"""
    
    def set_logging_state(self, logging: bool) -> None:
        """Updates logging state and LED indicator"""
    
    def publish_camera_status(self) -> None:
        """Publishes camera connection status and IP address"""
    
    def battery_loop(self) -> None:
        """Periodically publishes battery voltage (every 5 minutes)"""
```

#### MQTT Topics Subscribed

- `Camera.set_overlay` - Change active overlay
- `Camera.get_overlays` - Request list of available overlays
- `WirelessModule.all().module` - All wireless module messages (start/data/stop)
- `Camera.flip_video_feed/{device}` - Rotate video feed

#### MQTT Topics Published

- `Camera.status_camera/{device}` - Camera connection status
- `Camera.status_camera/{device}/battery` - Battery voltage
- `WirelessModule.{id}.start` / `stop` - Logging control commands
- `V3.start` - V3 compatibility start command

#### State Management

- Tracks `currently_logging` boolean
- Detects missed start messages by counting data messages
- Updates hardware LEDs based on state

---

### 2. Overlay System

The overlay system is responsible for displaying telemetry data over the camera feed.

#### Base Overlay Class (`overlay.py`)

The `Overlay` abstract base class provides the framework for all overlay implementations.

##### Three-Layer Rendering System

1. **Base Layer** (`base_canvas`): Static elements drawn once when overlay starts

   - Labels, borders, static text
   - Drawn in `_draw_base_layer()` method
2. **Data Layer** (`data_canvas`): Dynamic telemetry updated regularly

   - Power, speed, cadence, etc.
   - Updated in `_update_data_layer()` method
   - Refresh rate controlled by `data_update_interval` (default: 1 second)
3. **Message Layer** (`message_canvas`): Temporary messages/alerts

   - Dashboard messages, disconnect warnings
   - Automatically cleared when messages expire

##### Key Methods

```python
class Overlay(ABC):
    def _draw_base_layer(self):
        """Override to draw static overlay elements"""
    
    def _update_data_layer(self):
        """Override to update dynamic data display"""
    
    def get_data_func(self, data_key: str, decimals=0, scalar=1):
        """Helper to create data accessor functions"""
    
    def time_func(self, _: Data) -> str:
        """Returns elapsed time since overlay started (mm:ss format)"""
```

##### MQTT Integration

- Subscribes to data topics from `Data.get_topics()`
- Subscribes to `Camera.recording` for start/stop commands
- Publishes video feed status and recording status

##### Backend Integration

The overlay uses a backend factory to select the appropriate video backend:

- **PiCamera**: On Raspberry Pi (ARM architecture)
- **OpenCV**: On development machines (x86_64)
- **OpenCV Static Image**: For testing without camera (`--bg` flag)

---

### 3. Backend System (`backend/`)

Backends handle video capture, overlay compositing, and recording.

#### Backend Interface (`backend.py`)

Abstract base class defining the backend contract:

```python
class Backend(ABC):
    def start_video(self) -> None:
        """Start video capture and display"""
    
    def stop_video(self) -> None:
        """Stop video and release resources"""
    
    def _on_base_canvas_updated(self, base_canvas: Canvas) -> None:
        """Update base overlay layer"""
    
    def _on_canvases_updated(self, data_canvas, message_canvas) -> None:
        """Update data and message overlay layers"""
    
    def _on_loop(self) -> None:
        """Called every frame - may be blocking"""
    
    def start_recording(self) -> None:
        """Start H.264 recording to recordings/ folder"""
    
    def stop_recording(self) -> None:
        """Stop and save recording"""
```

#### PiCamera Backend (`picamera_backend.py`)

**Platform**: Raspberry Pi only (ARM architecture)

**Features**:

- Uses PiCamera library for hardware-accelerated video
- Native overlay support via `PiCamera.add_overlay()`
- Multiple overlay layers with z-ordering
- Direct hardware preview (no windowing)

**Layer System**:

```python
class PiCameraOverlayLayer(Enum):
    video_feed = 2  # Bottom layer
    base = 3
    data = 4
    message = 5     # Top layer
```

**Recording**: Records directly to H.264 format using PiCamera's native recording

**Limitations**:

- Only works on Raspberry Pi
- Requires `picamera` library
- Overlay updates require removing and re-adding overlays (due to PiCamera bug)

#### OpenCV Backend (`opencv_backend.py`)

**Platform**: Development machines (x86_64, macOS, Windows)

**Features**:

- Uses OpenCV's `VideoCapture` for webcam access
- Manual frame-by-frame compositing
- Window-based display (`cv2.imshow`)
- 60 FPS target framerate

**Compositing Process**:

1. Capture frame from webcam
2. Apply rotation if configured
3. Resize to viewport size
4. Composite base canvas
5. Composite data canvas
6. Composite message canvas
7. Display in window

**Recording**: Uses OpenCV's `VideoWriter` (codec-dependent)

#### OpenCV Static Image Backend (`opencv_static_image_backend.py`)

**Purpose**: Development and testing without camera hardware

**Features**:

- Loads static image as background
- Same compositing pipeline as OpenCV backend
- Useful for overlay development

**Usage**: Pass `--bg /path/to/image.jpg` to overlay script

---

### 4. Data System (`data.py`)

The data system handles parsing and storing telemetry data from MQTT messages.

#### DataValue Class

Represents a single data field with time-based expiration:

```python
class DataValue:
    def __init__(self, data_type: type, time_to_expire: int = 5):
        """Create data value with expiration time in seconds"""
    
    def update(self, value: Any) -> None:
        """Update value and timestamp"""
    
    def get(self) -> Any:
        """Get value if still valid, else None"""
    
    def get_string(self, decimals: int = 0, scalar: int = 1) -> str:
        """Get formatted string representation"""
    
    def is_valid(self) -> bool:
        """Check if data is still within expiration window"""
```

**Expiration Logic**:

- Default expiration: 5 seconds
- Data becomes invalid if not updated within expiration window
- Prevents stale data from being displayed

#### Data Classes

##### Base Data Class

```python
class Data(ABC):
    def __init__(self):
        self.data = {
            "power": DataValue(int),
            "cadence": DataValue(int),
            "heartRate": DataValue(int),
            "gps_speed": DataValue(float),
            "ant_speed": DataValue(float),
            "reed_velocity": DataValue(float),
            # ... more fields
        }
        self.logging = DataValue(bool, time_to_expire=3600)
        self.message = DataValue(str, 20)
```

**Data Fields**:

- **DAS Data**: `power`, `cadence`, `heartRate`, `gps`, `gps_speed`
- **ANT+ Data**: `ant_speed`, `ant_distance`
- **Reed Switch**: `reed_velocity`, `reed_distance`
- **Power Model**: `rec_power`, `rec_speed`, `predicted_max_speed`, `max_speed_achieved`, `zdist`, `plan_name`
- **System**: `voltage`, `logging`, `message`

##### DataV3 Implementation

Parses V3 bike MQTT message format:

```python
class DataV3(Data):
    def load_data(self, topic: str, data: str) -> None:
        """Parse MQTT message and update data fields"""
    
    def load_sensor_data(self, data: str) -> None:
        """Parse wireless module sensor data"""
    
    def load_recommended_sp(self, data: str) -> None:
        """Parse recommended speed/power from BOOST"""
```

**Message Format** (Wireless Module):

```json
{
  "sensors": [
    {"type": "power", "value": 250},
    {"type": "cadence", "value": 90},
    {"type": "gps", "value": {"speed": 35.5}},
    {"type": "antSpeed", "value": 35.2}
  ]
}
```

**Topic Matching**:

- Uses `topics.WirelessModule.all().data.matches(topic)` for pattern matching
- Handles start/stop messages to track logging state
- Detects missed start messages by counting data messages

---

### 5. Hardware Abstraction Layer (`hardware/hal.py`)

The HAL provides a unified interface to bike-specific hardware.

#### HardwareAbstractionLayer Interface

```python
class HardwareAbstractionLayer(ABC):
    @property
    def display_power_led(self) -> LED:
        """LED indicating display power state"""
    
    @property
    def mqtt_connected_led(self) -> LED:
        """LED indicating MQTT connection status"""
    
    @property
    def logging_led(self) -> LED:
        """LED indicating data logging state"""
    
    @property
    def logging_button(self) -> Switch:
        """Button to toggle logging state"""
    
    @property
    def display_power_switch(self) -> Switch:
        """Switch to turn display on/off"""
    
    @property
    def battery_adc(self) -> ADC:
        """ADC for battery voltage monitoring"""
```

#### V2HAL Implementation

**Hardware Configuration**:

- Display Power LED: GPIO 17 (pin 11, green)
- MQTT LED: Not present (uses `NopLED`)
- Logging LED: GPIO 27 (pin 13, red)
- Logging Button: GPIO 5 (pin 29, pull-down)
- Display Power Switch: GPIO 22 (pin 15)
- Battery ADC: Not present (uses `DummyADC`)

#### V3HAL Implementation

**Hardware Configuration**:

- Display Power LED: GPIO 17 (pin 11, green)
- MQTT LED: GPIO 18 (pin 24, yellow) - **NEW**
- Logging LED: GPIO 27 (pin 13, red)
- Logging Button: GPIO 5 (pin 29, pull-down)
- Display Power Switch: GPIO 22 (pin 15)
- Battery ADC: MCP3008 via SPI (real implementation)

#### Hardware Components

##### LED (`hardware/led.py`)

```python
class LED(ABC):
    def turn_on(self) -> None:
        """Turn LED on"""
    
    def turn_off(self) -> None:
        """Turn LED off"""
```

**Implementations**:

- `PhysicalLED`: Real GPIO control (Raspberry Pi)
- `DummyLED`: Print statements (development)
- `NopLED`: No-op (for missing hardware)

##### Switch (`hardware/switch.py`)

```python
class Switch:
    def read(self) -> bool:
        """Read current switch state"""
    
    async def wait_for_state(self, state: bool):
        """Wait for switch to reach specified state"""
    
    def create_interrupt(self, callback: Callable):
        """Register callback for switch state changes"""
```

**Pull-up/Down Configuration**:

- Logging button: Pull-down (active high)
- Display switch: Default (pull-up)

##### ADC (`hardware/adc.py`)

```python
class ADC(ABC):
    def read(self) -> float:
        """Read voltage value"""
```

**V3 Implementation**:

- Uses MCP3008 10-bit ADC via SPI
- Reads battery voltage through voltage divider
- Returns voltage in volts

---

### 6. Canvas System (`canvas.py`)

The canvas provides a drawing API for creating overlay graphics.

#### Canvas Class

```python
class Canvas:
    def __init__(self, width: int, height: int):
        """Create transparent canvas"""
    
    def clear(self) -> None:
        """Clear canvas to transparent"""
    
    def draw_text(self, text, coord, size=1.5, colour=Colour.black, align="left"):
        """Draw text on canvas"""
    
    def draw_rect(self, top_left: Coord, bottom_right: Coord, colour: Colourlike):
        """Draw filled rectangle"""
    
    def draw_circle(self, center: Coord, radius: float, colour: Colourlike):
        """Draw filled circle"""
    
    def copy_to(self, dest: np.ndarray) -> np.ndarray:
        """Composite canvas onto destination image with transparency"""
```

#### Features

**Transparency Support**:

- Uses BGRA format (Blue, Green, Red, Alpha)
- Alpha channel controls transparency
- Minimum alpha threshold (180) for visibility

**Text Rendering**:

- Uses OpenCV's `FONT_HERSHEY_SIMPLEX`
- Automatic thickness calculation based on size
- Alignment options: `left`, `right`, `centre`
- Coordinate system: Top-left is origin

**Color System**:

```python
class Colour(Enum):
    white = (255, 255, 255, 255)
    black = (0, 0, 0, 255)
    transparentBlack = (0, 0, 0, 0)
    semiTransparentBlack = (0, 0, 0, 181)
    blue = (255, 0, 0, 255)  # BGR format
    green = (0, 255, 0, 255)
    red = (0, 0, 255, 255)
    yellow = (0, 255, 255, 0)
```

**Compositing**:

- `copy_to()` method handles alpha blending
- Masks out transparent areas
- Preserves destination where canvas is transparent

---

### 7. Component System (`components/`)

Reusable UI components for building overlays.

#### Component Interface

```python
class Component(ABC):
    def draw_base(self, canvas: Canvas):
        """Draw static elements"""
    
    def draw_data(self, canvas: Canvas, data: Data):
        """Draw dynamic data"""
```

#### Available Components

##### DataField (`components/data_field.py`)

Simple data field with title and value:

```python
DataField(
    title="Power",
    value_func=lambda data: data["power"].get_string(decimals=0),
    coordinate=(x, y),
    is_title_static=True
)
```

**Features**:

- Right-aligned text
- Title in smaller font (0.8x)
- Data in larger font (1.5x)
- Automatic spacing

##### SpeedField

Specialized data field that prefers GPS speed, falls back to reed or ANT+:

```python
SpeedField(coordinate=(x, y))
```

**Priority Order**:

1. GPS speed
2. Reed velocity
3. ANT+ speed

**Dynamic Title**: Changes based on available data source

##### VoltageField

Voltage display with color coding:

- White: ≥ 7.3V (good)
- Yellow: 7.0V - 7.3V (medium)
- Red: < 7.0V (low)

##### Other Components

- `CentrePower`: Large centered power display
- `LoggingIndicator`: Visual indicator for logging state
- `DashboardMessage`: Displays messages from dashboard
- `DASDisconnectMessage`: Warning when DAS disconnects
- `TransparentRectangle`: Semi-transparent background rectangle

---

### 8. Configuration System (`config.py`)

Manages configuration from JSON file and environment variables.

#### Configuration Sources

1. **`configs.json`**: Runtime configuration

   - `activeOverlay`: Currently active overlay file
   - `rotation`: Video rotation in degrees (0, 90, 180, 270)
2. **`.env` file**: Environment-specific settings

   - `MHP_CAMERA`: Device identifier (e.g., "primary", "secondary")
   - `MHP_BIKE`: Bike version ("V2" or "V3")
   - `BROKER_IP`: MQTT broker IP address
   - `VIEWPORT_SIZE`: Screen resolution as "width,height"

#### Configuration Functions

```python
def read_configs(directory=CURRENT_DIRECTORY) -> dict:
    """Read and merge configs from JSON and .env"""
  
def set_overlay(new_overlays, directory=CURRENT_DIRECTORY):
    """Set active overlay for device"""
  
def set_rotation(rotation, directory=CURRENT_DIRECTORY):
    """Set video rotation"""
  
def get_active_overlay(directory=CURRENT_DIRECTORY) -> str:
    """Get path to active overlay file"""
  
def get_overlays(directory=CURRENT_DIRECTORY) -> list:
    """Get list of available overlay files"""
```

#### Default Values

- `BROKER_IP`: "192.168.100.100"
- `MHP_BIKE`: "V3"
- `VIEWPORT_SIZE`: (1024, 600)
- `BATTERY_PUBLISH_INTERVAL`: 300 seconds (5 minutes)

---

### 9. Switch Handler (`switch.py`)

Monitors physical display power switch and controls overlay process.

#### Functionality

```python
async def main():
    # Check initial switch state
    if hal.display_power_switch.read() == switch_on_state:
        enable()  # Start overlay
  
    # Monitor switch changes
    while True:
        await hal.display_power_switch.wait_for_state(not switch_on_state)
        disable()  # Stop overlay
    
        await hal.display_power_switch.wait_for_state(switch_on_state)
        enable()  # Start overlay
```

#### Process Management

- Uses `subprocess.Popen` to launch overlay process
- Kills process when switch is turned off
- Handles cleanup on exit

#### Systemd Service

Runs as `raspicam-switch.service`:

- Starts on boot
- Monitors switch continuously
- Automatically restarts on failure

---

### 10. Error Handling (`camera_error_handler.py`)

Context manager for graceful error handling.

```python
class CameraErrorHandler:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Publish error details to MQTT if exception occurred"""
```

**Error Publishing**:

- Publishes to `Camera.errors` topic
- Includes camera ID, backend, traceback, and config
- Allows remote monitoring of camera errors

**Usage**:

```python
with self.exception_handler:
    # Code that might fail
    self._draw_base_layer()
```

---

## Data Flow

### 1. System Startup

```
1. Raspberry Pi boots
2. systemd starts services:
   - raspicam-orchestrator.service
   - raspicam-switch.service
3. Orchestrator connects to MQTT broker
4. Orchestrator publishes camera status (online, IP address)
5. Switch handler monitors physical switch
6. When switch ON: overlay process starts
7. Overlay connects to MQTT, initializes backend
8. Overlay draws base layer, begins data updates
```

### 2. Data Reception and Display

```
1. Bike sensors send data via MQTT
2. Orchestrator receives wireless module messages
3. Orchestrator updates logging state if needed
4. Overlay receives data messages
5. DataV3.load_data() parses JSON
6. DataValue.update() stores value with timestamp
7. Overlay._update_data_layer() called every second
8. Canvas draws updated values
9. Backend composites canvases onto video frame
10. Display updated frame
```

### 3. Logging Control

```
User presses logging button
  ↓
Orchestrator.toggle_logging() called
  ↓
Publishes start/stop to wireless modules
  ↓
Publishes to V3.start topic
  ↓
Wireless modules receive command
  ↓
Modules start/stop logging
  ↓
Modules publish start/data/stop messages
  ↓
Orchestrator receives messages
  ↓
Updates logging state and LED
```

### 4. Recording Flow

```
MQTT message: Camera.recording_start
  ↓
Overlay.on_recording_message()
  ↓
Backend.start_recording()
  ↓
Creates H.264 file in recordings/ folder
  ↓
Backend._start_recording() (backend-specific)
  ↓
Recording status published every 60 seconds
  ↓
MQTT message: Camera.recording_stop
  ↓
Backend.stop_recording()
  ↓
File saved, status published
```

---

## Configuration

### Environment Variables (`.env`)

Create a `.env` file in the project root:

```bash
# Device identifier (used in MQTT topics)
MHP_CAMERA=primary

# Bike version (V2 or V3)
MHP_BIKE=V3

# MQTT broker IP address
BROKER_IP=192.168.100.100

# Display resolution (width,height)
VIEWPORT_SIZE=1024,600
```

### Runtime Configuration (`configs.json`)

Created automatically on first run:

```json
{
  "activeOverlay": "overlay_all_stats.py",
  "rotation": 0
}
```

**Setting Overlay via MQTT**:

```json
{
  "primary": "overlay_all_stats.py",
  "secondary": "overlay_top_strip.py"
}
```

### Overlay Selection

Overlays are discovered automatically by pattern matching `overlay_*.py` files.

**Available Overlays** (examples):

- `overlay_all_stats.py`: Comprehensive statistics display
- `overlay_top_strip.py`: Minimal top bar overlay
- `overlay_blank.py`: No overlay (camera only)
- `overlay_error.py`: Error display overlay
- `overlay_new.py`: New overlay template

---

## Development Guide

### Setting Up Development Environment

1. **Install Python 3.7** (required for OpenCV compatibility)

   ```bash
   pyenv install 3.7.7
   pyenv local 3.7.7
   ```
2. **Install Poetry**

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
3. **Install Dependencies**

   ```bash
   poetry install --dev
   ```
4. **Enter Poetry Shell**

   ```bash
   poetry shell
   ```
5. **Create `.env` File**

   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

### Running Overlays Locally

**With Webcam**:

```bash
python overlay_all_stats.py --host 192.168.100.100
```

**With Static Background** (for testing without camera):

```bash
python overlay_all_stats.py --bg /path/to/image.jpg --host 192.168.100.100
```

**Specify Bike Version**:

```bash
python overlay_all_stats.py --bike V3 --host 192.168.100.100
```

### Creating a New Overlay

1. **Create Overlay File**:

   ```python
   from overlay import Overlay
   from canvas import Colour

   class MyOverlay(Overlay):
       def _draw_base_layer(self):
           # Draw static elements
           self.base_canvas.draw_text("My Overlay", (10, 50))

       def _update_data_layer(self):
           # Update dynamic data
           self.data_canvas.clear()
           power = self.data["power"].get_string(decimals=0)
           self.data_canvas.draw_text(power, (10, 100))

   if __name__ == "__main__":
       args = Overlay.get_overlay_args("My custom overlay")
       overlay = MyOverlay(args.bike, args.bg)
       overlay.connect(ip=args.host)
   ```
2. **Test Locally**:

   ```bash
   python my_overlay.py --bg test_image.jpg
   ```
3. **Deploy**: Copy file to Raspberry Pi, set as active overlay via MQTT

### Using Components

```python
from components import DataField, SpeedField
from overlay import Overlay

class MyOverlay(Overlay):
    def __init__(self, bike=None, bg=None):
        super().__init__(bike, bg)
    
        # Create components
        self.power_field = DataField(
            "Power",
            self.get_data_func("power", decimals=0),
            (100, 200)
        )
        self.speed_field = SpeedField((100, 300))
  
    def _draw_base_layer(self):
        self.power_field.draw_base(self.base_canvas)
        # SpeedField has no base (dynamic title)
  
    def _update_data_layer(self):
        self.data_canvas.clear()
        self.power_field.draw_data(self.data_canvas, self.data)
        self.speed_field.draw_data(self.data_canvas, self.data)
```

### Testing

**Run All Tests**:

```bash
pytest
```

**Run Specific Test**:

```bash
pytest tests/orchestrator_test.py
```

**Test Files**:

- `tests/orchestrator_test.py`: Orchestrator functionality
- `tests/overlay_test.py`: Overlay base class
- `tests/test_data.py`: Data parsing

### Debugging

**MQTT Message Testing**:

```bash
# Terminal 1: Run overlay
python overlay_all_stats.py

# Terminal 2: Send test messages
python utils/mqtt_message_test.py
```

**View Logs** (on Raspberry Pi):

```bash
# Orchestrator logs
systemctl --user status raspicam-orchestrator

# Switch handler logs
systemctl --user status raspicam-switch

# View live logs
journalctl --user -u raspicam-orchestrator -f
```

---

## Deployment

### Raspberry Pi Setup

1. **Install System Dependencies**:

   ```bash
   sudo apt install libgtk-3-0 libavformat58 libtiff5 libcairo2 \
     libqt4-test libpango-1.0-0 libopenexr23 libavcodec58 \
     libilmbase23 libatk1.0-0 libpangocairo-1.0-0 libwebp6 \
     libqtgui4 libavutil56 libjasper1 libqtcore4 \
     libcairo-gobject2 libswscale5 libgdk-pixbuf2.0-0
   ```
2. **Clone Repository**:

   ```bash
   git clone <repository-url>
   cd raspicam_v4
   ```
3. **Install Python Dependencies**:

   ```bash
   poetry install
   ```
4. **Configure Environment**:

   ```bash
   cp .env.example .env
   nano .env  # Edit with Pi-specific settings
   ```
5. **Install Systemd Services**:

   ```bash
   ./service/install.sh
   ```
6. **Enable and Start Services**:

   ```bash
   systemctl --user enable --now raspicam-orchestrator
   systemctl --user enable --now raspicam-switch
   ```

### Service Files

**`raspicam-orchestrator.service`**:

```ini
[Unit]
Description=MHP Raspicam Orchestrator
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/orchestrator.py
Restart=always
WorkingDirectory=/path/to/raspicam_v4

[Install]
WantedBy=default.target
```

**`raspicam-switch.service`**:

```ini
[Unit]
Description=MHP Raspicam Switch Handler
After=raspicam-orchestrator.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /path/to/switch.py
Restart=always
WorkingDirectory=/path/to/raspicam_v4

[Install]
WantedBy=default.target
```

### VNC Setup (for Remote Development)

If running overlays over VNC:

1. Right-click VNC icon in system tray
2. Options → Troubleshooting
3. Enable "Direct capture mode"
4. Click OK

This allows PiCamera preview to work over VNC.

---

## API Reference

### MQTT Topics

#### Camera Topics

- `Camera.status_camera/{device}`: Camera connection status

  - Published by: Orchestrator
  - Format: `{"connected": true, "ipAddress": "192.168.100.1"}`
  - Retained: Yes
- `Camera.status_camera/{device}/battery`: Battery voltage

  - Published by: Orchestrator
  - Format: `{"voltage": 7.4}`
  - Retained: Yes
  - Interval: Every 5 minutes
- `Camera.status_video_feed/{device}`: Video feed status

  - Published by: Overlay
  - Format: `{"online": true}`
  - Retained: Yes
- `Camera.status_recording/{device}`: Recording status

  - Published by: Overlay
  - Format: `{"status": "recording", "recordingMinutes": 5.2, "recordingFile": "rec_1.h264", "diskSpaceRemaining": 1234567890}`
  - Retained: Yes
  - Interval: Every 60 seconds
- `Camera.set_overlay`: Set active overlay

  - Subscribed by: Orchestrator
  - Format: `{"primary": "overlay_all_stats.py", "secondary": "overlay_top_strip.py"}`
- `Camera.get_overlays`: Request overlay list

  - Subscribed by: Orchestrator
  - Response: `Camera.push_overlays` with config JSON
- `Camera.flip_video_feed/{device}`: Rotate video feed

  - Subscribed by: Orchestrator
  - Format: Empty message (toggles 180°)
- `Camera.recording`: Recording control

  - Subscribed by: Overlay
  - Topics: `Camera.recording_start`, `Camera.recording_stop`
- `Camera.overlay_message`: Display message on overlay

  - Format: `{"message": "Hello World"}`
- `Camera.errors`: Error reports

  - Published by: Overlay (via error handler)
  - Format: `{"camera": "primary", "backend": "picamera", "traceback": "...", "message": "..."}`

#### Wireless Module Topics

- `WirelessModule.{id}.start`: Start logging
- `WirelessModule.{id}.data`: Sensor data
- `WirelessModule.{id}.stop`: Stop logging
- `WirelessModule.all().start`: All modules start
- `WirelessModule.all().data`: All modules data
- `WirelessModule.all().stop`: All modules stop

#### BOOST Topics (Power Model)

- `BOOST.recommended_sp`: Recommended speed/power

  - Format: `{"power": 250, "speed": 35.5, "zoneDistance": 100}`
- `BOOST.predicted_max_speed`: Predicted maximum speed

  - Format: `{"speed": 40.2}`
- `BOOST.max_speed_achieved`: Maximum speed achieved

  - Format: `{"speed": 38.5}`

### Data Fields Reference

#### Available Data Fields

```python
# DAS Data
data["power"]              # int, watts
data["cadence"]            # int, RPM
data["heartRate"]          # int, BPM
data["gps"]                # int, GPS lock status
data["gps_speed"]          # float, km/h
data["ant_speed"]          # float, km/h
data["ant_distance"]       # float, meters
data["reed_velocity"]      # float, km/h
data["reed_distance"]      # float, meters

# Power Model
data["rec_power"]          # float, watts (recommended)
data["rec_speed"]          # float, km/h (recommended)
data["predicted_max_speed"] # float, km/h
data["max_speed_achieved"]  # float, km/h
data["zdist"]              # float, zone distance
data["plan_name"]          # str, power plan name

# System
data["voltage"]            # float, volts
data.logging               # bool, logging state
data.message               # str, dashboard message
```

#### Data Access Methods

```python
# Check if data is valid
if data["power"].is_valid():
    value = data["power"].get()

# Get formatted string
power_str = data["power"].get_string(decimals=0)  # "250"
speed_str = data["gps_speed"].get_string(decimals=1, scalar=1)  # "35.5"

# Check logging state
if data.is_logging():
    # Logging is active

# Check for messages
if data.has_message():
    message = data.get_message()
```

### Canvas API

```python
# Create canvas
canvas = Canvas(width=1024, height=600)

# Clear canvas
canvas.clear()

# Draw text
canvas.draw_text("Hello", (x, y), size=1.5, colour=Colour.white, align="left")

# Draw shapes
canvas.draw_rect((x1, y1), (x2, y2), colour=Colour.red)
canvas.draw_circle((x, y), radius=10, colour=Colour.blue)

# Composite onto image
output = canvas.copy_to(video_frame)
```

### Backend API

```python
# Backend is used as context manager
with backend:
    backend.on_base_canvas_updated(base_canvas)
    backend.on_canvases_updated(data_canvas, message_canvas)
    backend.on_loop()  # Called every frame
    backend.start_recording()
    backend.stop_recording()
```

---

## Troubleshooting

### Common Issues

#### 1. Overlay Not Starting

**Symptoms**: No video feed, overlay process exits immediately

**Solutions**:

- Check MQTT broker connectivity: `ping <broker_ip>`
- Verify `.env` file exists and has correct `BROKER_IP`
- Check systemd logs: `journalctl --user -u raspicam-orchestrator -n 50`
- Verify camera is connected (if using PiCamera backend)
- Test with static image: `python overlay_all_stats.py --bg test.jpg`

#### 2. No Data Displaying

**Symptoms**: Overlay shows but all values are "--"

**Solutions**:

- Verify MQTT broker is receiving data from bike
- Check overlay is subscribed to correct topics
- Verify data expiration time (default 5 seconds)
- Check `data.py` parsing logic matches message format
- Use MQTT test utility to send test messages

#### 3. PiCamera Not Working

**Symptoms**: `RuntimeError: picamera library unavailable`

**Solutions**:

- Verify running on Raspberry Pi (not development machine)
- Check `picamera` library installed: `pip list | grep picamera`
- Verify camera is enabled: `raspi-config` → Interface Options → Camera
- Check camera cable connection
- Try OpenCV backend for testing: modify `overlay.py` to force OpenCV

#### 4. Recording Not Working

**Symptoms**: Recording status shows "error" or doesn't start

**Solutions**:

- Check disk space: `df -h`
- Verify `recordings/` folder exists and is writable
- Check file permissions
- Review recording status message for specific error
- Verify backend supports recording (PiCamera, OpenCV)

#### 5. LEDs Not Working

**Symptoms**: LEDs don't turn on/off

**Solutions**:

- Verify running on Raspberry Pi (not development machine)
- Check GPIO pin assignments in `hal.py` match hardware
- Verify `RPi.GPIO` library installed
- Check LED wiring and connections
- Test with `DummyLED` to verify code path

#### 6. Switch Not Responding

**Symptoms**: Physical switch doesn't start/stop overlay

**Solutions**:

- Check `raspicam-switch.service` is running: `systemctl --user status raspicam-switch`
- Verify switch wiring and GPIO pin
- Check switch handler logs: `journalctl --user -u raspicam-switch -f`
- Test switch reading manually with GPIO test script

#### 7. MQTT Connection Issues

**Symptoms**: Orchestrator/overlay can't connect to broker

**Solutions**:

- Verify broker is running: `mosquitto_pub -h <broker_ip> -t test -m "test"`
- Check network connectivity: `ping <broker_ip>`
- Verify firewall allows port 1883
- Check `.env` has correct `BROKER_IP`
- Review MQTT client logs for connection errors

#### 8. Overlay Rotation Issues

**Symptoms**: Video feed is rotated incorrectly

**Solutions**:

- Check `configs.json` for `rotation` value
- Send flip command via MQTT: `mosquitto_pub -h <broker> -t Camera/flip_video_feed/primary -m ""`
- Verify backend supports rotation (PiCamera, OpenCV)
- Check rotation values: 0, 90, 180, 270 degrees

### Debugging Tips

1. **Enable Verbose Logging**:

   - Uncomment print statements in `orchestrator.py` and `overlay.py`
   - Check MQTT message callbacks
2. **Test Components Individually**:

   - Run overlay with `--bg` flag to isolate video issues
   - Test data parsing separately
   - Verify MQTT messages with `mosquitto_sub`
3. **Use Development Backend**:

   - Force OpenCV backend on Pi for debugging
   - Use static image backend for overlay development
4. **Monitor System Resources**:

   - Check CPU usage: `top`
   - Check memory: `free -h`
   - Check disk space: `df -h`
5. **Verify Configuration**:

   - Print configs: `python config.py`
   - Check active overlay: `cat configs.json`
   - Verify environment variables: `env | grep MHP`

---

## Additional Resources

### Project Structure Reference

```
raspicam_v4/
├── backend/                 # Video backends
│   ├── backend.py           # Abstract base class
│   ├── backend_factory.py   # Backend factory
│   ├── picamera_backend.py # Raspberry Pi backend
│   ├── opencv_backend.py   # Development backend
│   └── opencv_static_image_backend.py
├── components/             # Reusable UI components
│   ├── component.py        # Base component class
│   ├── data_field.py       # Data display components
│   └── ...
├── hardware/               # Hardware abstraction
│   ├── hal.py             # Hardware abstraction layer
│   ├── led.py             # LED control
│   ├── switch.py          # Switch handling
│   └── adc.py             # Analog-to-digital converter
├── service/               # Systemd service files
│   ├── install.sh         # Service installer
│   └── *.service          # Service definitions
├── tests/                 # Unit tests
├── utils/                 # Utility scripts
├── orchestrator.py        # Main orchestrator service
├── switch.py              # Switch handler
├── overlay.py             # Base overlay class
├── overlay_*.py           # Overlay implementations
├── data.py                # Data handling
├── config.py              # Configuration management
├── canvas.py              # Drawing API
└── camera_error_handler.py # Error handling
```

### Key Design Patterns

1. **Factory Pattern**: `BackendFactory`, `DataFactory`
2. **Abstract Base Classes**: `Backend`, `Overlay`, `Data`, `Component`, `HAL`
3. **Strategy Pattern**: Multiple backend implementations
4. **Observer Pattern**: MQTT message callbacks
5. **Context Manager**: Error handling, backend lifecycle

### Performance Considerations

- **Data Update Interval**: Default 1 second (configurable in overlay)
- **Recording Status**: Published every 60 seconds
- **Battery Status**: Published every 5 minutes
- **Video Framerate**: 60 FPS target (OpenCV), hardware-accelerated (PiCamera)
- **Canvas Compositing**: Alpha blending can be CPU-intensive

### Security Notes

- MQTT broker should be on isolated network
- No authentication in current implementation (assumes trusted network)
- File permissions on `recordings/` folder should be restricted
- Service files run as user (not root) for security

---

## Version History

- **V4**: Current version with modular overlay system, multi-backend support
- **V3**: Previous version (referenced for data format compatibility)

---

## Contributing

See README.md for contribution guidelines. The `master` branch is write-protected to ensure stability.

---

*Documentation Version: 1.0*

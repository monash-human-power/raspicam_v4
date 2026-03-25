# Project overview

## What the project does

Python application for **Monash Human Power (MHP) “Raspicam”**: a Raspberry Pi–based **live camera feed** with **telemetry overlays** (power, cadence, speeds, messages, etc.), integrated with the team stack via **MQTT** (`mhp` / `paho-mqtt`) and optional **SocketCAN** for V4-style data.

## Core problem it solves

Riders and pit crew need a **reliable on-bike display** that shows **DAS / wireless-module / BOOST** data on top of video, exposes **camera/recording status** on MQTT, and ties **physical controls** (display power switch, logging button, LEDs, battery sense) to the same ecosystem.

## Key features (from code)

- **Video + layered overlays**: `Canvas` (BGRA) + `BackendFactory` → `PiCameraBackend` (ARM), `OpenCVBackend` (dev), or `OpenCVStaticImageBackend` (`--bg`) — see `overlay.py`, `backend/`.
- **MQTT data pipeline**: `DataMQTT` subscribes to WM start/data/stop, overlay messages, battery, BOOST topics — `data_mqtt.py`.
- **Orchestrator**: separate long-running process for MQTT: logging toggle publish, overlay selection via `config.set_overlay`, overlay list push, video flip/rotation, camera + battery status — `orchestrator.py`.
- **Hardware abstraction**: `V2HAL` / `V3HAL` — LEDs, logging button, display power switch, battery ADC — `hardware/hal.py`.
- **Display power switch process control**: `switch.py` spawns/kills overlay subprocess when the physical switch toggles.
- **H.264 recording** on Pi: `PiCameraBackend._start_recording` / `_stop_recording` — `backend/picamera_backend.py`.
- **Error reporting**: `CameraErrorHandler` publishes to `Camera.errors` — `camera_error_handler.py`.
- **Multiple overlay UIs**: e.g. `overlay_all_stats.py`, `overlay_top_strip.py`, `overlay_blank.py`, `overlay_new.py`, `overlay_error.py`.

## Target users

MHP **engineering team** maintaining Pi displays; **developers** testing with webcam/static image; **operators** using systemd on-bike (`service/`). Not a general consumer app.

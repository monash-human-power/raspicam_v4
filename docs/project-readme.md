# MHP Raspicam — project README (documentation copy)

This is the **engineering documentation copy** of a production-style README. The repository’s primary entry remains **[README.md](../README.md)** at the repo root (includes contributors, historical install notes).

---

## Description

Live camera overlays for the Monash Human Power (MHP) vehicle display: video from a Raspberry Pi camera or dev webcam, telemetry from MQTT (and experimental CAN for V4), plus GPIO integration for LEDs, logging, and the display power switch.

## Features

- Layered overlays (base / data / message) composited on the camera feed
- MQTT integration via shared `mhp` topic definitions (DAS, wireless modules, BOOST, camera status)
- Raspberry Pi: `picamera` preview + overlays; optional H.264 recording to `recordings/`
- Development: OpenCV webcam or static background image (`--bg`)
- Orchestrator process: remote overlay selection, logging control, battery telemetry, camera online status
- Hardware abstraction for V2/V3 Pi wiring (LEDs, switches, battery ADC)

## Tech stack

- Python (see `pyproject.toml` for supported versions)
- Poetry for dependencies
- OpenCV, Paho MQTT, `mhp` (Monash Human Power common topics)
- Raspberry Pi: picamera, RPi.GPIO, MCP3xxx (V3 battery)
- Optional: python-can (SocketCAN) for V4-oriented experiments

## Prerequisites

- Poetry
- For Pi: OS packages for OpenCV (see distribution docs)
- Access to the private `mhp` package (SSH key to GitHub or CI-style HTTPS token)
- `.env` for broker, bike, camera role, viewport

## Installation

1. Clone the repository and install dependencies:

   ```bash
   poetry install
   ```

   Use the appropriate Poetry group/extras flags for your Poetry version (e.g. dev dependencies).

2. Copy `.env.example` to `.env` and set:

   - `MHP_CAMERA` — device key (e.g. primary / secondary; used when setting overlays remotely)
   - `MHP_BIKE` — `V2`, `V3`, or `V4` (V4 CAN path is still being hardened)
   - `BROKER_IP` — MQTT broker address
   - `VIEWPORT_SIZE` — `width,height` in pixels

3. **Configuration file:** On first run, **`configs.json`** is created if missing (see `config.py`). It stores the active overlay script and optional rotation. Remote MQTT commands can update it via `config.set_overlay` / `set_rotation` (used by the orchestrator).

## How to run

Activate the virtual environment (e.g. `poetry shell`), then:

**Overlay only (development)**

```bash
python overlay_all_stats.py --host <broker_ip> [--bike V3] [--bg path/to/image.png]
```

**Orchestrator (bike / integration)**

```bash
python orchestrator.py --host <broker_ip>
```

**Display power switch** (toggles overlay subprocess — intended for Pi with HAL)

```bash
python switch.py --host <broker_ip>
```

**Tests**

```bash
pytest
```

**Systemd (Raspberry Pi)**

```bash
./service/install.sh
systemctl --user enable --now raspicam-orchestrator
systemctl --user enable --now raspicam-switch
```

## Project structure (brief)

- `overlay.py` — overlay base class and main loop
- `overlay_*.py` — concrete UIs
- `backend/` — picamera / OpenCV / static image backends
- `data_*.py` — telemetry ingestion (MQTT vs CAN)
- `hardware/` — GPIO HAL
- `orchestrator.py`, `switch.py` — long-running control processes
- `service/` — systemd user unit templates

## Future improvements

- Complete V4 CAN decoding and align with `hal` / CLI
- Expand automated integration tests (MQTT / CAN mocks)
- CI refresh (Python version, action versions) aligned with `pyproject.toml`

## Contributors

See the All Contributors section in the root [README.md](../README.md).

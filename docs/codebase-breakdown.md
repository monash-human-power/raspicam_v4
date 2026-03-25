# Codebase breakdown

## High-level architecture

- **Embedded single-board (Pi) + desktop dev**: not microservices. **Two main runtime roles** on the bike: **`orchestrator.py`** (MQTT + GPIO) and **`switch.py`** (asyncio + subprocess overlay), plus **overlay scripts** as separate processes.
- **MQTT** is the integration bus with the rest of MHP (`mhp` package from `monash-human-power/common`).
- **Optional CAN**: `DataCANbus` uses `python-can` + `Notifier` (`data_canbus.py`).

## Folder / file structure (major pieces)

| Area | Role |
|------|------|
| **Root** (`overlay.py`, `overlay_*.py`) | `Overlay` ABC: canvas stack, MQTT client for camera topics, backend loop, data refresh interval. Concrete overlays implement `_draw_base_layer` / `_update_data_layer`. |
| **`backend/`** | `Backend` ABC: video lifecycle, compositing hooks, recording + status, disk usage in status. Factories in `backend_factory.py`. |
| **`components/`** | Reusable overlay UI pieces (`Component` ABC, messages, fields, etc.) — compositional pattern for building UIs. |
| **`hardware/`** | GPIO LEDs, switches, MCP3xxx ADC path for V3 battery, `get_hal()` / `cleanup()`. |
| **`utils/`** | e.g. `mqtt_message_test.py` — manual MQTT publish helper for overlay messages. |
| **`service/`** | `systemd` user unit templates + `install.sh` (copies units, appends `WorkingDirectory`). |
| **`tests/`** | `pytest` for `DataValue`, `DataFactory`, `DataMQTT` parsing, overlay instantiation smoke tests, orchestrator args. |
| **`recordings/`** | `.gitignore` — PiCamera writes `rec_*.h264` under project via `backend/backend.py`. |

## Key modules and responsibilities

- **`config.py`**: Loads **`configs.json`**, merges **`.env`** (`MHP_CAMERA`, `MHP_BIKE`, `BROKER_IP`, `VIEWPORT_SIZE`), lists `overlay_*.py`, `set_overlay` / `set_rotation` for remote MQTT updates. **Note:** the root README refers to `config.json`; code uses **`configs.json`**.
- **`data.py` / `datavalue.py`**: Central schema of `DataValue` fields + expiry; `Data` ABC with `load_data`.
- **`datafactory.py`**: `v2`/`v3` → `DataMQTT`; `v4` → `DataCANbus`. **`overlay.py` CLI `--bike` choices are only `v2`/`v3`** — no `v4` in argparse while factory supports `v4`.
- **`orchestrator.Orchestrator`**: MQTT subscriptions for overlay control, WM logging state sync, `get_ip()` for camera status, `battery_loop()` timer publishing ADC voltage.
- **`canvas.Canvas`**: OpenCV drawing + alpha compositing via `copy_to`.

## Data flow (typical MQTT path)

1. **Telemetry** published on WM / BOOST / overlay message / battery topics.
2. **`DataMQTT.connect()`** → broker; **`_on_connect`** subscribes **`get_topics()`**; callbacks → **`load_data`** → updates **`Data`**.
3. **`Overlay.connect()`** (in `overlay.py`) starts MQTT loop for **camera** client, runs **`BackendFactory.create`** `with` backend, loop: every `data_update_interval` (1s default) calls **`update_data_layer`** → **`backend.on_canvases_updated`**.
4. **Orchestrator** (separate process) does **not** drive the overlay canvas; it handles **logging**, **overlay file selection**, **flip**, **status topics**.

## Design patterns (evident)

- **Abstract base classes**: `Overlay`, `Backend`, `Data`, `Component`, `HardwareAbstractionLayer`.
- **Factory**: `BackendFactory`, `DataFactory`.
- **Context managers**: `Backend.__enter__` / `__exit__`, `CameraErrorHandler` for exception → MQTT error topic.
- **Template method**: `Overlay` defines loop; subclasses implement `_draw_base_layer` / `_update_data_layer`.

## External dependencies (`pyproject.toml`)

- **Runtime**: `opencv-python`, `paho-mqtt`, `python-dotenv`, **`mhp`** (git `common`), **`python-can`**, **`msgpack`**, **`virtualcan`** (git), Pi-only: **`picamera`**, **`RPi.GPIO`**, **`adafruit-circuitpython-mcp3xxx`** (markers for ARM).

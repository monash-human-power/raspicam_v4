# Current implementation status

## Fully implemented / coherent

- **V2/V3 MQTT data path** (`DataMQTT`), parsing tests in `tests/test_data.py`.
- **Overlay framework**, **PiCamera** and **OpenCV** backends, **static image** dev backend.
- **Orchestrator** MQTT behavior, **HAL** for V2/V3, **switch** overlay lifecycle.
- **Recording** on **`PiCameraBackend`** only; status JSON over MQTT.

## Partial / incomplete / risky

- **V4 / CAN** (`DataCANbus`): `connect()` is a no-op; **`load_data` uses `msg.arbitration_id == 0x124` for many branches** — only the **first** branch runs; rest is dead code. `load_message_json` / JSON loaders expect **string**-like payloads in places but may receive **bytes** from CAN. Comment in file: *“will need to be changed”*.
- **`hal.get_hal()`**: only **`v2`/`v3`** — **`v4` raises `ValueError`**, while `DataFactory.create("v4")` returns `DataCANbus` → **inconsistent** if `.env` uses `MHP_BIKE=V4`.
- **`DataMQTT` TODOs**: avoid reading configs every `get_topics()` call; **`topics.BOOST.generate_complete`** not handled.
- **Docs drift**: README **Python 3.7** and **`config.json`** vs **`pyproject.toml` `python = ">=3.8"`** and **`configs.json`**. **`.python-version`** is **3.8**. CI (`.github/workflows/run_tests.yml`) uses **Python 3.7** — likely **incompatible** with current `pyproject.toml` constraint unless CI is outdated.
- **`switch.py`**: uses `subprocess.Popen.kill(overlay_process)` — unusual style; works in Python if `Popen.kill` is invoked correctly but is non-idiomatic vs `overlay_process.kill()`.
- **`OpenCVBackend`**: `cv2.cv2.ROTATE_*` in `opencv_backend.py` — likely a bug (typically `cv2.ROTATE_*`); worth verifying on a run.

## Technical debt / practices visible

- **`CameraErrorHandler.__exit__`**: checks `exc_type is Exception` — does not catch **`BaseException`** subclasses outside `Exception`.
- **Duplicate / exploratory files**: `note.md` documents removed exception handling in `DataMQTT` (intentional for debugging).
- **Private git dependency** `mhp` via SSH — CI uses token rewrite in `run_tests.yml`; local dev needs access pattern documented.

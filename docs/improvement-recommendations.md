# Improvement recommendations

## Architecture

- **Unify V4 story**: today **`DataFactory` + `DataCANbus`** and **`hal` + orchestrator** disagree on supported bikes — resolve before shipping V4.
- **Consider one MQTT client for overlay data** vs camera control, or document why two clients in `Overlay` + `DataMQTT` are required (latency, topic isolation).

## Performance

- **PiCamera overlay strategy** already notes recreating overlays instead of `update()` due to picamera 1.13 issues — if Pi stack upgrades, revisit to reduce churn.
- **`data_update_interval` = 1s** may be coarse for some signals; make configurable per overlay or via `.env`.

## Scalability

- System is **per-display embedded**; scaling is **ops** (many Pis), not horizontal service scaling. MQTT broker capacity and **retained** status topics are the main shared resources.

## Code quality

- Remove or quarantine **dead CAN branches** in `data_canbus.py` and add **typing** / **tests** for `DataCANbus`.
- Align **exception handling** in `DataMQTT` with production needs (see `note.md` in repo root).
- Run **lint/format** consistently; `pyproject.toml` pins black/flake8/pylint — ensure CI runs them (see `.github/workflows/linting.yml`).

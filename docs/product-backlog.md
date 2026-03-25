# Product backlog

Structured backlog based on the current codebase state.

## Core features

| Title | Description | Priority | Effort | Dependencies |
|-------|-------------|----------|--------|--------------|
| Align V4 bike end-to-end | Decide single source of truth: either extend **`get_hal("v4")`** (or stub HAL), add **`--bike v4`** to overlay CLI, and document **CAN** setup, or remove **`v4`** from `DataFactory` until ready. | High | Medium | Hardware spec for V4 |
| Fix `DataCANbus` arbitration & payloads | Replace duplicate `0x124` branches with real IDs; define byte layout; fix JSON vs bytes for CAN; add graceful failure if `can0` missing. | High | Large | CAN matrix from EE/firmware |
| Single config filename story | Update README and examples to **`configs.json`** or rename in code to match README — pick one. | Medium | Small | None |
| Python version alignment | Reconcile **README**, **`.python-version`**, **`pyproject.toml`**, and **CI** (3.7 vs ≥3.8). | High | Small | CI secrets for `mhp` |

## Enhancements

| Title | Description | Priority | Effort | Dependencies |
|-------|-------------|----------|--------|--------------|
| BOOST `generate_complete` | Implement handler in `DataMQTT` per TODO. | Low | Medium | Topic contract in `mhp` |
| Cache config in `DataMQTT.get_topics()` | Avoid `read_configs()` every call. | Low | Small | None |
| Overlay using `Component` library | Migrate heavy overlays to `components/` for reuse. | Medium | Large | UX agreement |

## Technical improvements

| Title | Description | Priority | Effort | Dependencies |
|-------|-------------|----------|--------|--------------|
| OpenCV rotation API fix | Verify and fix `cv2.cv2.ROTATE_*` in `opencv_backend.py`. | Medium | Small | Dev machine with webcam |
| Disk space path in recording status | `disk_usage(Path(__file__).parent)` uses **`backend/`** — confirm if project root was intended. | Low | Small | None |
| `switch.py` subprocess cleanup | Use idiomatic `terminate`/`kill`, handle zombie children. | Medium | Small | None |
| Dependency install docs | Document SSH vs HTTPS for `mhp`, Poetry 2.x vs `poetry install --with dev` (README still says `--dev`). | Medium | Small | Poetry version |

## Testing & QA

| Title | Description | Priority | Effort | Dependencies |
|-------|-------------|----------|--------|--------------|
| CI Python version fix | Match `pyproject.toml`; cache strategy for Poetry. | High | Small | GitHub secrets |
| Integration test with MQTT | Mock broker or testcontainers for `DataMQTT` subscribe/load. | Medium | Large | None |
| `DataCANbus` unit tests | Mock `can.Bus` / frame injection. | High | Medium | Fixed IDs/layout |
| Orchestrator tests beyond construction | Mock MQTT to test `on_message` branches. | Low | Medium | None |

## DevOps / deployment

| Title | Description | Priority | Effort | Dependencies |
|-------|-------------|----------|--------|--------------|
| Refresh GitHub Actions | `actions/checkout@v2`, `setup-python@v1` — update to supported versions; pin Python. | Medium | Small | None |
| Document `systemd` user vs system | `install.sh` uses **user** units; README already mentions `systemctl --user` — add troubleshooting (linger, permissions). | Low | Small | None |
| VNC / Pi capture | README already notes VNC direct capture — keep as ops runbook. | Low | Small | None |

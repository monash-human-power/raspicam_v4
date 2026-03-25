# Suggested 2-week sprint plan

## Week 1 — stability and source of truth

1. **Python + CI alignment** — fix version mismatch so `poetry install` and CI match `pyproject.toml` (unblocks every contributor).
2. **Config naming** — one name for JSON config; update root README.
3. **Quick OpenCV verification** — webcam path for devs (`opencv_backend.py` rotation APIs).

## Week 2 — V4 scope or honest gating

4. Either **stub or implement V4 HAL + CLI** and **fix `DataCANbus`** with real IDs and tests, **or** gate `v4` behind a feature flag and document “not production-ready.”
5. **Add CAN unit tests** once IDs are fixed.
6. **Optional**: `generate_complete` handling or config caching in `DataMQTT` if time remains.

## Sequencing rationale

CI and version docs are **blocking** for any team. V4 work depends on **frozen** CAN semantics — avoid coding IDs until hardware/firmware agrees.

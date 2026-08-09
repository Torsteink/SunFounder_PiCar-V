# PiCar-V Agent Guide

## Project context

- This repository controls a physical SunFounder PiCar-V running Raspberry Pi OS.
- The active deployment branch is `V3.0`; the Pi normally pulls that branch from
  `origin` (`Torsteink/SunFounder_PiCar-V`).
- The current remote-control stack is Python 3, Django 5.2, Flask 3.1, OpenCV,
  and the SunFounder `picar` package. Ignore README statements describing a
  Python 2/Django 1.9 runtime; those describe the original upstream project.
- Development may happen on a machine that is not the Pi. Never claim that a
  camera, servo, motor, I2C, GPIO, power, or full application check passed unless
  it was actually run on the Pi.

## Repository map

- `remote_control/`: active Django web controller.
- `remote_control/remote_control/views.py`: command routing and hardware setup.
- `remote_control/remote_control/picar_v_video_stream.py`: OpenCV capture and
  Flask MJPEG stream on port 8765 by default.
- `remote_control/remote_control/driver/`: pan/tilt camera driver and calibration
  data.
- `remote_control/remote_control/templates/templates/run.html`: browser controls.
- `ball_track/`: standalone legacy ball-tracking program; it is not part of the
  Django server.
- `mjpg-streamer/`: bundled legacy binaries and web assets; the current Django
  remote uses the Flask/OpenCV streamer instead.
- `install_dependencies`: Raspberry Pi OS installer. It creates `venv/` with
  `--system-site-packages` because OpenCV is installed by `apt`.

## Setup and operation

Run installation only on the Raspberry Pi, and only when the user asks for it:

```bash
./install_dependencies
```

Start the controller on the Pi:

```bash
cd remote_control
./start
```

The server listens on port 8000. The MJPEG server listens on port 8765 unless
`PICAR_STREAM_PORT` overrides it.

Supported runtime configuration:

- `PICAR_CAMERA_SOURCE` (default `0`; prefer `/dev/v4l/by-id/...` when present)
- `PICAR_CAMERA_RECONNECT_DELAY` (default `0.5` seconds)
- `PICAR_CAMERA_MAX_RECONNECT_DELAY` (default `5` seconds)
- `PICAR_CAMERA_READ_FAILURE_LIMIT` (default `3`)
- `PICAR_STREAM_PORT` (default `8765`)
- `PICAR_DEFAULT_SPEED` (default `60`)
- `PICAR_I2C_BUS` (default `1`)
- `PICAR_CONFIG_PATH` (default driver calibration file)
- `PICAR_VENV` and `PYTHON` for dependency installation
- `DJANGO_SECRET_KEY` and `DJANGO_DEBUG`

Do not commit secrets, machine-specific device names, or local virtual
environments.

## Development workflow

- Inspect the working tree before editing and preserve unrelated user changes.
- Keep changes compatible with Python 3 on Raspberry Pi OS. Match nearby style;
  do not reformat legacy files wholesale as part of a focused fix.
- Prefer environment variables over new hard-coded machine paths or device IDs.
- Avoid adding dependencies unless they are necessary on the Pi and reflected in
  `requirements.txt` or `install_dependencies`, as appropriate.
- Do not edit bundled `mjpg-streamer` binaries or generated artifacts unless the
  task explicitly concerns them.
- Do not commit, push, install packages, alter boot configuration, or change
  calibration values unless the user requests that action.

## Validation

Use the strongest checks available in the current environment, and report what
could not be exercised.

For every Python change:

```bash
python3 -m compileall -q remote_control ball_track
git diff --check
```

When the repository virtual environment is available:

```bash
cd remote_control
../venv/bin/python manage.py check
../venv/bin/python manage.py test
```

There is currently no meaningful automated hardware test suite. Mocked tests
may validate control flow, but they do not replace Pi-side checks.

For camera or power faults, gather evidence on the Pi while reproducing:

```bash
sudo dmesg -wT
vcgencmd get_throttled
ls -l /dev/video* /dev/v4l/by-id/*
```

Distinguish an application failure from a device disappearing, USB reset,
undervoltage, cable movement, or power noise.

## Hardware safety and invariants

- Do not move motors or servos during automated tests without explicit user
  authorization and confirmation that the car is in a safe position.
- Ensure rear-wheel motion is stopped in cleanup paths after hardware tests.
- Preserve calibration data in `remote_control/remote_control/driver/config` and
  `remote_control/db.sqlite3` unless calibration/database work is requested.
- Only one process may own an OpenCV `VideoCapture` for a camera device. Keep
  camera/stream worker startup idempotent.
- A failed camera pipeline must release the capture and reopen it with bounded
  retries; a dead pipeline must not spin continuously or freeze forever.
- Keep `/run/?action=...` and speed responses lightweight. Browser command calls
  ignore the body and should return `204` after successful handling.
- Keep hardware initialization thread-safe and idempotent. Multiple browser
  requests must not create competing workers or reinitialize hardware.
- Preserve support for both numeric camera indexes and stable `/dev/v4l/by-id/`
  paths.

## Code review rules

- Flag any change that can create multiple camera owners, duplicate Flask
  stream servers, or repeated hardware initialization.
- Flag camera read loops that fail to release/reopen after persistent errors or
  that retry without a delay.
- Flag motor-control paths that can leave the rear wheels running after an
  exception or interrupted test.
- Flag claims of successful hardware verification when only local static or
  mocked checks were performed.
- Flag hard-coded host paths, camera device numbers, I2C buses, secrets, or
  deployment addresses when an existing configuration variable should be used.

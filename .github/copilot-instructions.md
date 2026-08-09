# PiCar-V repository instructions

Read and follow `AGENTS.md`; it is the canonical project guide.

- This code controls physical Raspberry Pi hardware. Never move motors or servos
  in an automated test without explicit user authorization.
- Development often runs away from the Pi. Clearly distinguish syntax, mocked,
  and local checks from camera, GPIO, I2C, servo, motor, USB, and power checks
  actually performed on the Pi.
- The active stack is Python 3, Django 5.2, Flask 3.1, OpenCV, and SunFounder's
  `picar` package. Legacy Python 2/Django 1.9 README text is not authoritative.
- Keep camera capture single-owner, worker startup idempotent, and failed capture
  recovery release/reopen based with bounded delays.
- Preserve lightweight `204` responses for successful `/run` control commands.
- Prefer existing `PICAR_*` and `DJANGO_*` environment settings over hard-coded
  device names, paths, ports, credentials, or I2C bus numbers.
- Run `python3 -m compileall -q remote_control ball_track` and
  `git diff --check`. When `venv/` exists, also run Django's `check` and `test`
  commands described in `AGENTS.md`.
- Do not claim hardware validation unless it was performed on the Raspberry Pi.
- Keep focused changes small and do not reformat unrelated legacy code.

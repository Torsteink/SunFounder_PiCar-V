#!/usr/bin/env python3

from pathlib import Path
import subprocess
import time


CONFIG_PATHS = (Path("/boot/firmware/config.txt"), Path("/boot/config.txt"))


def boot_config_path():
    for path in CONFIG_PATHS:
        if path.exists():
            return path
    return CONFIG_PATHS[0]


def enabled_i2c_buses():
    return sorted(Path("/dev").glob("i2c-*"))


def ensure_i2c_enabled(config_path):
    lines = config_path.read_text().splitlines()
    active_lines = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]
    if "dtparam=i2c_arm=on" in active_lines:
        return False

    with config_path.open("a") as config_file:
        config_file.write("\ndtparam=i2c_arm=on\n")
    return True


def run_i2cdetect(bus_number):
    subprocess.run(["i2cdetect", "-y", str(bus_number)], check=False)


def main():
    print("")
    print("   ====================================")
    print("   ||                                ||")
    print("   ||     Raspberry Pi I2C check     ||")
    print("   ||                                ||")
    print("   ====================================")
    print("")
    time.sleep(1)

    buses = enabled_i2c_buses()
    if buses:
        print("   I2C devices exposed by Linux:")
        for bus in buses:
            print("   - {0}".format(bus))
        print("")
        for bus in buses:
            bus_number = bus.name.split("-", 1)[1]
            print("   Running i2cdetect on bus {0}...".format(bus_number))
            run_i2cdetect(bus_number)
        return

    config_path = boot_config_path()
    print("   No /dev/i2c-* device was found.")
    print("   Checking {0}".format(config_path))

    if not config_path.exists():
        print("   Boot config file does not exist. Enable I2C with raspi-config.")
        return

    changed = ensure_i2c_enabled(config_path)
    if changed:
        print("   Added dtparam=i2c_arm=on.")
        answer = input("   Reboot now? (y/n) ")
        if answer.lower() == "y":
            print("   Rebooting...")
            subprocess.run(["sudo", "reboot"], check=False)
        else:
            print("   Reboot later for the change to take effect.")
    else:
        print("   I2C is already enabled in config. Reboot or check overlays/hardware.")


if __name__ == "__main__":
    main()

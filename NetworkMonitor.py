#!/usr/bin/env python3
"""
==============================================================
  Resort Network Connectivity Logger
  Author : IT Operations
  Purpose: Ping critical devices, log outages, repeat every 60s
==============================================================
"""

import csv
import subprocess
import datetime
import time
import platform
import os
import sys

# ── File paths ──────────────────────────────────────────────
DEVICES_FILE  = "devices.csv"
OUTAGE_LOG    = "network_outages.log"

# ── ANSI colour codes (work on macOS, Linux, Windows 10+) ───
RESET   = "\033[0m"
BOLD    = "\033[1m"
GREEN   = "\033[92m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
DIM     = "\033[2m"

# ── Ping interval (seconds) ──────────────────────────────────
CHECK_INTERVAL = 60


# ────────────────────────────────────────────────────────────
def enable_windows_ansi():
    """Enable ANSI escape codes on Windows 10+."""
    if platform.system() == "Windows":
        os.system("")           # Activates VT100 mode in cmd / PowerShell


def ping(ip: str) -> bool:
    """
    Ping an IP address once.
    Returns True if the host responds, False otherwise.
    Uses the correct flag for the OS (-n on Windows, -c on Unix).
    """
    flag = "-n" if platform.system() == "Windows" else "-c"

    result = subprocess.run(
        ["ping", flag, "1", ip],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0


def log_outage(ip: str, device_name: str, location: str) -> None:
    """Append a single outage entry to the log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] OUTAGE | {device_name} | {location} | {ip}\n"

    with open(OUTAGE_LOG, "a") as log_file:
        log_file.write(line)


def load_devices(filepath: str) -> list[dict]:
    """Read devices.csv and return a list of device dicts."""
    devices = []
    try:
        with open(filepath, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                devices.append({
                    "ip":       row["IP_Address"].strip(),
                    "location": row["Location"].strip(),
                    "name":     row["Device_Name"].strip(),
                })
    except FileNotFoundError:
        print(f"{RED}ERROR:{RESET} '{filepath}' not found. "
              "Place it in the same directory as this script.")
        sys.exit(1)
    except KeyError as e:
        print(f"{RED}ERROR:{RESET} Missing column in CSV: {e}")
        sys.exit(1)

    return devices


def print_header(cycle: int) -> None:
    """Print a formatted scan header."""
    now   = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    width = 62

    print()
    print(f"{CYAN}{'═' * width}{RESET}")
    print(f"{CYAN}  RESORT NETWORK MONITOR{RESET}   "
          f"{DIM}Cycle #{cycle}   {now}{RESET}")
    print(f"{CYAN}{'═' * width}{RESET}")
    print(
        f"  {BOLD}{WHITE}{'DEVICE':<25}{'LOCATION':<22}{'STATUS'}{RESET}"
    )
    print(f"{DIM}  {'─' * 58}{RESET}")


def print_device_status(name: str, location: str, ip: str, is_up: bool) -> None:
    """Print a colour-coded status line for one device."""
    if is_up:
        status_str = f"{GREEN}{BOLD}● UP  {RESET}"
    else:
        status_str = f"{RED}{BOLD}DOWN  {RESET}"

    # Truncate long names/locations so columns stay tidy
    name_col     = (name[:22]     + "…") if len(name)     > 23 else name
    location_col = (location[:19] + "…") if len(location) > 20 else location

    print(f"  {WHITE}{name_col:<25}{DIM}{location_col:<22}{RESET}"
          f"{status_str}  {DIM}{ip}{RESET}")


def print_summary(total: int, up: int, down: int) -> None:
    """Print a summary footer after each scan cycle."""
    width = 62
    print(f"{DIM}  {'─' * 58}{RESET}")
    print(f"  {BOLD}Summary:{RESET}  "
          f"{GREEN}{up} UP{RESET}  |  "
          f"{RED}{down} DOWN{RESET}  |  "
          f"{WHITE}{total} Total{RESET}")
    if down > 0:
        print(f"  {YELLOW}⚠  Outages logged → {OUTAGE_LOG}{RESET}")
    print(f"{CYAN}{'═' * width}{RESET}")
    print(f"  {DIM}Next scan in {CHECK_INTERVAL}s … (Ctrl+C to stop){RESET}")


# ────────────────────────────────────────────────────────────
def run_scan(devices: list[dict], cycle: int) -> None:
    """Ping every device in the list and log any failures."""
    up_count   = 0
    down_count = 0

    print_header(cycle)

    for device in devices:
        ip       = device["ip"]
        name     = device["name"]
        location = device["location"]

        is_up = ping(ip)

        print_device_status(name, location, ip, is_up)

        if is_up:
            up_count += 1
        else:
            down_count += 1
            log_outage(ip, name, location)

    print_summary(len(devices), up_count, down_count)


# ────────────────────────────────────────────────────────────
def main() -> None:
    enable_windows_ansi()

    print(f"\n{CYAN}{BOLD}  Initialising Resort Network Monitor …{RESET}")
    print(f"  {DIM}Loading devices from '{DEVICES_FILE}'{RESET}")

    devices = load_devices(DEVICES_FILE)

    print(f"  {GREEN}✔ {len(devices)} devices loaded.{RESET}  "
          f"{DIM}Outages → '{OUTAGE_LOG}'{RESET}\n")

    cycle = 1

    try:
        while True:
            run_scan(devices, cycle)
            cycle += 1
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}Monitor stopped by user. Goodbye!{RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
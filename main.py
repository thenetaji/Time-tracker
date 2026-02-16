#!/usr/bin/env python3


import json
import time
import signal
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path.home() / ".code_time_tracker"
SESSION_FILE = DATA_DIR / "current_session.json"
DAILY_FILE = Path.cwd() / "coding_time.txt"

AUTO_SAVE_INTERVAL = 10  


class TimeTracker:
    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)

        self.start_time = None
        self.total_seconds = 0
        self.is_running = False
        self.last_auto_save = time.time()

        self.load_session()

    def load_session(self):
        if SESSION_FILE.exists():
            try:
                data = json.loads(SESSION_FILE.read_text())

                self.start_time = (
                    datetime.fromisoformat(data["start_time"])
                    if data["start_time"]
                    else None
                )
                self.total_seconds = data["total_seconds"]
                self.is_running = data["is_running"]

                if self.is_running and self.start_time:
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    self.total_seconds += elapsed
                    self.start_time = datetime.now()
                    print("✓ Previous session recovered\n")

            except Exception:
                pass

    def save_session(self):
        data = {
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "total_seconds": self.total_seconds,
            "is_running": self.is_running,
        }
        SESSION_FILE.write_text(json.dumps(data))

    def start(self):
        if not self.is_running:
            self.start_time = datetime.now()
            self.is_running = True
            self.save_session()

    def stop(self):
        if self.is_running:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.total_seconds += elapsed
            self.is_running = False
            self.save_session()
            self.write_daily_time()

    def get_seconds(self):
        if self.is_running:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            return self.total_seconds + elapsed
        return self.total_seconds

    @staticmethod
    def format_hms(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @staticmethod
    def format_daily(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}hr {m}min"

    def write_daily_time(self):
        if self.total_seconds <= 0:
            return

        today = datetime.now().strftime("%d/%m/%y")
        new_entry = f"{today} - {self.format_daily(self.total_seconds)}\n"

        lines = []
        if DAILY_FILE.exists():
            lines = DAILY_FILE.read_text().splitlines()

        updated = False
        for i, line in enumerate(lines):
            if line.startswith(today):
                lines[i] = new_entry.strip()
                updated = True
                break

        if not updated:
            lines.append(new_entry.strip())

        DAILY_FILE.write_text("\n".join(lines) + "\n")

    def auto_save_check(self):
        now = time.time()
        if now - self.last_auto_save >= AUTO_SAVE_INTERVAL:
            self.save_session()
            self.last_auto_save = now


def print_header():
    print("=" * 40)
    print("      CODING TIME TRACKER")
    print("=" * 40)
    print("Press Ctrl+C to stop & save\n")


def exit_handler(tracker):
    tracker.stop()
    print("\n✓ Session saved to file. Bye!\n")
    sys.exit(0)


def main():
    tracker = TimeTracker()

    signal.signal(signal.SIGINT, lambda s, f: exit_handler(tracker))

    if not tracker.is_running:
        tracker.start()

    print_header()

    while True:
        seconds = tracker.get_seconds()
        print(f"\rTime Running: {tracker.format_hms(seconds)}", end="", flush=True)

        tracker.auto_save_check()
        time.sleep(1)


if __name__ == "__main__":
    main()

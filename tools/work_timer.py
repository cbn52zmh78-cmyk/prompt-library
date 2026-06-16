#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import time
import sys
from datetime import datetime

def start_timer(minutes=25):
    print(f"\n⏱️  Work timer started for {minutes} minutes.")
    print("Press Ctrl+C to stop early.\n")
    try:
        time.sleep(minutes * 60)
        print("\n✅ Time's up! Great work.")
    except KeyboardInterrupt:
        print("\n⏹️  Timer stopped early.")

if __name__ == "__main__":
    mins = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    start_timer(mins)
#!/usr/bin/env python3
"""
Coding Time Tracker
A persistent time tracking tool for coding sessions with automatic session recovery
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import signal
import sys

# Configuration
DATA_DIR = Path.home() / '.code_time_tracker'
SESSION_FILE = DATA_DIR / 'current_session.json'
HISTORY_FILE = DATA_DIR / 'history.json'
REPORT_FILE = Path.cwd() / 'report.txt'

class TimeTracker:
    def __init__(self):
        self.ensure_data_dir()
        self.start_time = None
        self.total_seconds = 0
        self.is_running = False
        self.load_session()
        
    def ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        DATA_DIR.mkdir(exist_ok=True)
        
    def load_session(self):
        """Load existing session if terminal was closed"""
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE, 'r') as f:
                    data = json.load(f)
                    self.start_time = datetime.fromisoformat(data['start_time'])
                    self.total_seconds = data['total_seconds']
                    self.is_running = data['is_running']
                    
                    if self.is_running:
                        # Add time that passed while terminal was closed
                        elapsed = (datetime.now() - self.start_time).total_seconds()
                        self.total_seconds += elapsed
                        self.start_time = datetime.now()
                        print("\n✓ Session recovered! Time tracked even while terminal was closed.\n")
            except Exception as e:
                print(f"Warning: Could not load previous session: {e}")
                
    def save_session(self):
        """Save current session to disk"""
        data = {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'total_seconds': self.total_seconds,
            'is_running': self.is_running
        }
        with open(SESSION_FILE, 'w') as f:
            json.dump(data, f)
            
    def start(self):
        """Start tracking time"""
        if not self.is_running:
            self.start_time = datetime.now()
            self.is_running = True
            self.save_session()
            
    def stop(self):
        """Stop tracking time"""
        if self.is_running:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.total_seconds += elapsed
            self.is_running = False
            self.save_session()
            self.save_to_history()
            
    def get_current_time(self):
        """Get current session time in seconds"""
        if self.is_running:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            return self.total_seconds + elapsed
        return self.total_seconds
    
    def format_time(self, seconds):
        """Format seconds into HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def save_to_history(self):
        """Save session to history"""
        history = []
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        
        if self.total_seconds > 0:
            history.append({
                'date': datetime.now().isoformat(),
                'duration_seconds': self.total_seconds
            })
            
            with open(HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2)
    
    def generate_report(self):
        """Generate monthly report"""
        if not HISTORY_FILE.exists():
            return "No tracking history found."
        
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
        
        # Group by month
        monthly_data = {}
        daily_data = {}
        
        for entry in history:
            date = datetime.fromisoformat(entry['date'])
            month_key = date.strftime('%Y-%m')
            day_key = date.strftime('%Y-%m-%d')
            
            if month_key not in monthly_data:
                monthly_data[month_key] = 0
            monthly_data[month_key] += entry['duration_seconds']
            
            if day_key not in daily_data:
                daily_data[day_key] = 0
            daily_data[day_key] += entry['duration_seconds']
        
        # Generate report
        report = []
        report.append("=" * 60)
        report.append("CODING TIME TRACKER - MONTHLY REPORT")
        report.append("=" * 60)
        report.append(f"\nReport Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Monthly summary
        report.append("-" * 60)
        report.append("MONTHLY SUMMARY")
        report.append("-" * 60)
        for month, seconds in sorted(monthly_data.items(), reverse=True):
            hours = seconds / 3600
            report.append(f"{month}: {self.format_time(seconds)} ({hours:.2f} hours)")
        
        # Current month daily breakdown
        current_month = datetime.now().strftime('%Y-%m')
        current_month_days = {k: v for k, v in daily_data.items() if k.startswith(current_month)}
        
        if current_month_days:
            report.append("\n" + "-" * 60)
            report.append(f"DAILY BREAKDOWN - {current_month}")
            report.append("-" * 60)
            for day, seconds in sorted(current_month_days.items(), reverse=True):
                hours = seconds / 3600
                report.append(f"{day}: {self.format_time(seconds)} ({hours:.2f} hours)")
        
        # Statistics
        total_seconds = sum(monthly_data.values())
        total_hours = total_seconds / 3600
        avg_per_day = total_seconds / len(daily_data) if daily_data else 0
        
        report.append("\n" + "-" * 60)
        report.append("STATISTICS")
        report.append("-" * 60)
        report.append(f"Total Time Tracked: {self.format_time(total_seconds)} ({total_hours:.2f} hours)")
        report.append(f"Total Sessions: {len(history)}")
        report.append(f"Total Days: {len(daily_data)}")
        report.append(f"Average per Day: {self.format_time(avg_per_day)} ({avg_per_day/3600:.2f} hours)")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def download_report(self):
        """Save report to file"""
        report = self.generate_report()
        with open(REPORT_FILE, 'w') as f:
            f.write(report)
        return str(REPORT_FILE)
    
    def reset_session(self):
        """Reset current session"""
        self.total_seconds = 0
        self.is_running = False
        self.start_time = None
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_big_time(time_str):
    """Print time in large ASCII art"""
    digits = {
        '0': ['███', '█ █', '█ █', '█ █', '███'],
        '1': [' █ ', '██ ', ' █ ', ' █ ', '███'],
        '2': ['███', '  █', '███', '█  ', '███'],
        '3': ['███', '  █', '███', '  █', '███'],
        '4': ['█ █', '█ █', '███', '  █', '  █'],
        '5': ['███', '█  ', '███', '  █', '███'],
        '6': ['███', '█  ', '███', '█ █', '███'],
        '7': ['███', '  █', '  █', '  █', '  █'],
        '8': ['███', '█ █', '███', '█ █', '███'],
        '9': ['███', '█ █', '███', '  █', '███'],
        ':': [' ', '█', ' ', '█', ' ']
    }
    
    lines = ['', '', '', '', '']
    for char in time_str:
        if char in digits:
            for i in range(5):
                lines[i] += digits[char][i] + '  '
    
    for line in lines:
        print(f"    {line}")

def display_ui(tracker):
    """Display the main UI"""
    clear_screen()
    
    current_time = tracker.get_current_time()
    time_str = tracker.format_time(current_time)
    
    print("\n" + "=" * 60)
    print("          CODING TIME TRACKER")
    print("=" * 60 + "\n")
    
    print_big_time(time_str)
    
    print("\n" + "-" * 60)
    if tracker.is_running:
        print("  Status: 🟢 TRACKING - Started, keep it open in background")
    else:
        print("  Status: 🔴 STOPPED")
    print("-" * 60)
    
    print("\nOptions:")
    print("  [1] Start Tracking")
    print("  [2] Stop & Save Session")
    print("  [3] Download Report (report.txt)")
    print("  [4] View Report")
    print("  [5] Reset Current Session")
    print("  [6] Exit")
    print("\nPress Ctrl+C to minimize (session continues in background)")
    print("=" * 60)

def handle_exit(tracker):
    """Handle graceful exit"""
    if tracker.is_running:
        tracker.save_session()
        print("\n✓ Session saved! Time tracking continues in background.")
        print("  Run this script again to see updated time.\n")
    else:
        print("\n✓ Goodbye!\n")

def main():
    tracker = TimeTracker()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        handle_exit(tracker)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Auto-start tracking
    if not tracker.is_running:
        tracker.start()
    
    while True:
        try:
            display_ui(tracker)
            
            if tracker.is_running:
                # Update display every second
                time.sleep(1)
                continue
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == '1':
                tracker.start()
                print("\n✓ Tracking started!")
                time.sleep(1)
            elif choice == '2':
                tracker.stop()
                print("\n✓ Session stopped and saved!")
                time.sleep(2)
            elif choice == '3':
                filepath = tracker.download_report()
                print(f"\n✓ Report saved to: {filepath}")
                time.sleep(2)
            elif choice == '4':
                clear_screen()
                print(tracker.generate_report())
                input("\nPress Enter to continue...")
            elif choice == '5':
                confirm = input("Reset current session? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    tracker.reset_session()
                    print("\n✓ Session reset!")
                    time.sleep(1)
            elif choice == '6':
                handle_exit(tracker)
                break
            else:
                print("\nInvalid choice!")
                time.sleep(1)
                
        except KeyboardInterrupt:
            handle_exit(tracker)
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
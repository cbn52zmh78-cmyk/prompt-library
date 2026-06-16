#!/usr/bin/env python3
"""
NEXUS Git Auto Pusher
Periodically commits and pushes changes in a git repo.
Run this in one dedicated terminal.
"""

import argparse
import subprocess
import time
import datetime
import sys

def run_git(args, cwd):
    """Run a git command and return output or None on error."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(f"[Git Error] {e.stderr.strip()}")
        return None

def auto_commit_push(repo_path, interval_minutes):
    print(f" Git Auto Pusher started")
    print(f"   Repo: {repo_path}")
    print(f"   Interval: {interval_minutes} minutes")
    print("   Press Ctrl+C to stop.\n")

    while True:
        try:
            # Check for changes
            status = run_git(["status", "--porcelain"], repo_path)
            
            if status:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Changes detected. Committing...")
                
                # Stage everything
                run_git(["add", "-A"], repo_path)
                
                # Commit with timestamp
                commit_msg = f"Auto commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                run_git(["commit", "-m", commit_msg], repo_path)
                
                # Push
                print("   Pushing to remote...")
                push_output = run_git(["push"], repo_path)
                
                if push_output:
                    print(f"   {push_output}")
                print("✅ Commit + Push complete.\n")
            else:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] No changes. Sleeping...\n")
            
            time.sleep(interval_minutes * 60)
            
        except KeyboardInterrupt:
            print("\n Git Auto Pusher stopped by user.")
            sys.exit(0)
        except Exception as e:
            print(f"[Error] {e}")
            time.sleep(60)  # Wait 1 min on unexpected error

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto commit + push git changes periodically.")
    parser.add_argument(
        "--path", 
        default=r"C:\Users\NCG\Videos\Grok Projects",
        help="Path to your git repository"
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        default=15,
        help="Minutes between checks (default: 15)"
    )
    args = parser.parse_args()
    
    auto_commit_push(args.path, args.interval)
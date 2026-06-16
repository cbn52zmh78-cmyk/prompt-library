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

def list_untracked(repo_path):
    """Return untracked, non-ignored paths relative to repo root."""
    output = run_git(["ls-files", "--others", "--exclude-standard"], repo_path)
    if output is None or not output:
        return []
    return [line for line in output.splitlines() if line.strip()]

def stage_all_changes(repo_path):
    """Stage modified, deleted, and untracked files."""
    untracked = list_untracked(repo_path)
    if untracked:
        print(f"   Untracked files ({len(untracked)}):")
        for path in untracked[:15]:
            print(f"     + {path}")
        if len(untracked) > 15:
            print(f"     ... and {len(untracked) - 15} more")

    return run_git(["add", "-A", "--", "."], repo_path) is not None

def auto_commit_push(repo_path, interval_minutes):
    print(f" Git Auto Pusher started")
    print(f"   Repo: {repo_path}")
    print(f"   Interval: {interval_minutes} minutes")
    print("   Press Ctrl+C to stop.\n")

    while True:
        try:
            # Check for changes
            status = run_git(["status", "--porcelain"], repo_path)
            if status is None:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Git status failed. Retrying...\n")
                time.sleep(60)
                continue

            if status:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Changes detected. Committing...")

                if not stage_all_changes(repo_path):
                    print("   Staging failed. Retrying next interval.\n")
                    time.sleep(interval_minutes * 60)
                    continue

                commit_msg = f"Auto commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                if run_git(["commit", "-m", commit_msg], repo_path) is None:
                    print("   Commit failed. Retrying next interval.\n")
                    time.sleep(interval_minutes * 60)
                    continue

                print("   Pushing to remote...")
                push_output = run_git(["push"], repo_path)
                if push_output is None:
                    print("   Push failed. Commit is local only.\n")
                    time.sleep(interval_minutes * 60)
                    continue

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
        default=5,
        help="Minutes between checks (default: 5)"
    )
    args = parser.parse_args()
    
    auto_commit_push(args.path, args.interval)
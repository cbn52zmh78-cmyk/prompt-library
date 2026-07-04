import sys
sys.path.insert(0, "/sessions/intelligent-sleepy-wright/mnt/DAVID/scripts")
try:
    from _paths import DAVID_ROOT, WORKSPACE
    print(f"DAVID_ROOT={DAVID_ROOT}")
    print(f"WORKSPACE={WORKSPACE}")
except ImportError as e:
    print(f"_paths import failed: {e}")

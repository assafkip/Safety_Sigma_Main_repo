#!/usr/bin/env python3
from pathlib import Path
from src.memory.reuse_index import build_or_update_index

def main():
    repo = Path(__file__).resolve().parents[1]
    path = build_or_update_index(repo_root=repo)
    print(f"Reuse index at: {path}")

if __name__ == "__main__":
    main()
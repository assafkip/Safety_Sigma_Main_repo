#!/usr/bin/env python3
from pathlib import Path
from src.agentic.orchestrator import Orchestrator

def main():
    repo = Path(__file__).resolve().parents[1]
    o = Orchestrator(repo)
    run_dir = o.run()
    print(f"Agentic run complete: {run_dir}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
serve.py — Serve both demo app versions on separate ports.

Usage:
    python serve.py

Version A (control)   → http://localhost:3001
Version B (treatment) → http://localhost:3002

Press Ctrl+C to stop both servers.
"""

import os
import sys
import threading
import http.server
import socketserver
from pathlib import Path

BASE = Path(__file__).parent

VERSION_A_PORT = 3003
VERSION_B_PORT = 3004


class SilentHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Suppress default request logs to keep output clean."""
    def log_message(self, format, *args):
        pass  # comment this out if you want access logs


def serve_directory(directory: Path, port: int, label: str):
    os.chdir(directory)
    with socketserver.TCPServer(("", port), SilentHTTPHandler) as httpd:
        print(f"  ✅  {label} → http://localhost:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════╗")
    print("║        AutoAB Demo App Server            ║")
    print("╠══════════════════════════════════════════╣")
    print("║  Starting both demo versions...          ║")
    print("╚══════════════════════════════════════════╝")
    print()

    thread_a = threading.Thread(
        target=serve_directory,
        args=(BASE / "version-a", VERSION_A_PORT, "Version A (control)  "),
        daemon=True,
    )
    thread_b = threading.Thread(
        target=serve_directory,
        args=(BASE / "version-b", VERSION_B_PORT, "Version B (treatment)"),
        daemon=True,
    )

    thread_a.start()
    thread_b.start()

    print("  ─────────────────────────────────────────")
    print("  📋  Next steps:")
    print("  1.  Start the backend:  docker compose up -d")
    print("  2.  Create an experiment via the API (see README)")
    print("  3.  Paste the experiment UUID into both index.html files")
    print("        → Replace REPLACE_WITH_EXPERIMENT_ID")
    print("  4.  Open both URLs and interact to generate events")
    print("  5.  Run the Locust simulator for bulk traffic:")
    print("        locust -f ../simulator/locustfile.py --headless -u 50 -r 5 --run-time 3m")
    print("  ─────────────────────────────────────────")
    print()
    print("  Press Ctrl+C to stop.\n")

    try:
        thread_a.join()
        thread_b.join()
    except KeyboardInterrupt:
        print("\n\n  Servers stopped. Goodbye!")
        sys.exit(0)

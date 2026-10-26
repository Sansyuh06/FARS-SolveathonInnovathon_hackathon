"""
FARSverse Desktop Launcher
==========================
Standalone launcher executable for FARSverse Autonomous Robotics Platform.
Spins up local services (Ollama, Backend Engine, Next.js Studio) and launches
a standalone desktop application window.
"""

import os
import sys
import time
import socket
import urllib.request
import urllib.error
import subprocess
import signal
import atexit
import webbrowser

# Determine base project root
if getattr(sys, "frozen", False):
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    if os.path.exists(os.path.join(exe_dir, "fars_platform")):
        PROJECT_ROOT = exe_dir
    elif os.path.exists(os.path.join(os.getcwd(), "fars_platform")):
        PROJECT_ROOT = os.getcwd()
    else:
        PROJECT_ROOT = r"d:\fyeshi\project\rohit"
else:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CHILD_PROCESSES = []

def cleanup_children():
    """Terminate any child processes started by this launcher."""
    for proc in CHILD_PROCESSES:
        try:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except Exception:
            pass

atexit.register(cleanup_children)

def signal_handler(sig, frame):
    print("\n[FARS] Shutting down all services...")
    cleanup_children()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, signal_handler)

def is_port_in_use(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.6)
        return s.connect_ex((host, port)) == 0

def check_http_endpoint(url, timeout=1.5):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FARS-Launcher"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 304, 307, 308)
    except Exception:
        return False

def wait_for_endpoint(url, desc, max_attempts=30, delay=1.0):
    print(f"[INIT] Waiting for {desc}...", end="", flush=True)
    for _ in range(max_attempts):
        if check_http_endpoint(url):
            print(" [READY]")
            return True
        print(".", end="", flush=True)
        time.sleep(delay)
    print(" [TIMED OUT]")
    return False

def find_browser_app_executable():
    """Finds Chrome or Edge to launch in standalone --app mode."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def main():
    print("=" * 65)
    print("       FARS STUDIO -- AUTONOMOUS ROBOTICS PLATFORM v2.5       ")
    print("=" * 65)
    print(f"Project Directory : {PROJECT_ROOT}")
    print(f"Platform          : Windows (x86_64)")
    print("-" * 65)

    # 1. Ollama AI Engine (Port 11434)
    print("[1/3] Checking Ollama AI Engine (Port 11434)...")
    if is_port_in_use(11434):
        print("  -> Ollama AI Engine is already active on 127.0.0.1:11434")
    else:
        print("  -> Starting Ollama service...")
        try:
            ollama_proc = subprocess.Popen(
                ["ollama", "serve"],
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                shell=True
            )
            CHILD_PROCESSES.append(ollama_proc)
            time.sleep(1.5)
        except Exception as e:
            print(f"  [WARN] Could not auto-start ollama: {e}")

    # 2. FARS Backend Engine (Port 8080)
    print("[2/3] Checking FARSverse Backend Simulation (Port 8080)...")
    if is_port_in_use(8080):
        print("  -> Backend simulation server is already active on 127.0.0.1:8080")
    else:
        print("  -> Starting Python simulation kernel...")
        backend_cmd = [sys.executable if getattr(sys, "frozen", False) else "python", "fars_platform/run.py", "--no-3d"]
        if getattr(sys, "frozen", False):
            backend_cmd = ["python", "fars_platform/run.py", "--no-3d"]
        
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=PROJECT_ROOT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            shell=True
        )
        CHILD_PROCESSES.append(backend_proc)
        time.sleep(2)

    # 3. FARS Next.js 3D Studio Frontend (Port 3000)
    print("[3/3] Checking FARSverse 3D Studio (Port 3000)...")
    frontend_dir = os.path.join(PROJECT_ROOT, "desktop", "farsy-main")
    if is_port_in_use(3000):
        print("  -> 3D Studio frontend is already active on localhost:3000")
    else:
        print("  -> Starting Next.js / Three.js 3D Studio...")
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            shell=True
        )
        CHILD_PROCESSES.append(frontend_proc)
        wait_for_endpoint("http://localhost:3000", "FARSverse Studio", max_attempts=25, delay=1.0)

    # 4. Launch Desktop Window
    print("-" * 65)
    print("[LAUNCH] Initializing FARS Studio Desktop Application Window...")
    target_url = "http://localhost:3000"
    browser_exe = find_browser_app_executable()

    if browser_exe:
        print(f"  -> Launching native standalone app window via {os.path.basename(browser_exe)}")
        app_flags = [
            browser_exe,
            f"--app={target_url}",
            "--window-size=1640,980",
            "--window-position=50,50",
            "--disable-infobars",
            "--disable-extensions",
            "--no-first-run",
        ]
        try:
            window_proc = subprocess.Popen(app_flags)
            CHILD_PROCESSES.append(window_proc)
        except Exception as e:
            print(f"  [WARN] Failed to launch in app mode: {e}, falling back to default browser.")
            webbrowser.open(target_url)
            window_proc = None
    else:
        print("  -> Launching default browser interface...")
        webbrowser.open(target_url)
        window_proc = None

    print("=" * 65)
    print(" FARS STUDIO v2.5 IS RUNNING")
    print(" - 3D Digital Twin   : http://localhost:3000")
    print(" - Simulation Kernel : http://127.0.0.1:8080")
    print(" - Ollama Local LLM  : http://127.0.0.1:11434")
    print("=" * 65)
    print("\nKeep this console window open to maintain background services.")
    print("To close FARS Studio, close the application window or press Ctrl+C here.\n")

    try:
        if window_proc:
            # Block until user closes the application window
            window_proc.wait()
            print("\n[FARS] Desktop application window closed.")
        else:
            # Keep alive
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        print("[FARS] Cleaning up services...")
        cleanup_children()
        print("[FARS] Shutdown complete. Goodbye.")

if __name__ == "__main__":
    main()

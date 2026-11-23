"""
Unified Launcher for:
1. CloudPulse 4-Page Demo Application (Port 5050)
2. DevOps Provider Bridge for Ansible, Nagios, Terraform (Port 9095)
3. InfraPilot Enterprise Control Plane (Port 8000)
"""
import sys
import os
import time
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_APP_DIR = os.path.join(BASE_DIR, "demo_app")
INFRAPILOT_DIR = os.path.join(BASE_DIR, "infrapilot")

# Ensure environment variable for DB
os.environ["INFRAPILOT_DB_PATH"] = os.path.join(BASE_DIR, "infrapilot_state.db")
os.environ["PYTHONPATH"] = f"{INFRAPILOT_DIR}{os.pathsep}{DEMO_APP_DIR}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"

print("=" * 70)
print("🚀 LAUNCHING FULL INFRAPILOT & DEVOPS ECOSYSTEM")
print("=" * 70)

python_exe = sys.executable

# 1. Start Demo Application
print("[1/3] Starting CloudPulse 4-Page Demo Application on http://127.0.0.1:5050 ...")
p_demo = subprocess.Popen(
    [python_exe, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5050"],
    cwd=DEMO_APP_DIR
)

# 2. Start DevOps Bridge
print("[2/3] Starting DevOps Provider Bridge (Ansible, Nagios, Terraform) on http://127.0.0.1:9095 ...")
p_bridge = subprocess.Popen(
    [python_exe, "-m", "uvicorn", "devops_bridge:app", "--host", "0.0.0.0", "--port", "9095"],
    cwd=DEMO_APP_DIR
)

# 3. Start InfraPilot Control Plane
print("[3/3] Starting InfraPilot Control Plane on http://127.0.0.1:8000 ...")
p_infra = subprocess.Popen(
    [python_exe, "-m", "uvicorn", "infrapilot.server:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=INFRAPILOT_DIR
)

time.sleep(3)
print("\n" + "=" * 70)
print("✅ ALL SERVICES ACTIVE AND READY:")
print("  - Demo Application (4 Pages): http://127.0.0.1:5050")
print("  - DevOps Provider Bridge:     http://127.0.0.1:9095")
print("  - InfraPilot Control Plane:   http://127.0.0.1:8000")
print("=" * 70 + "\n")

try:
    p_demo.wait()
    p_bridge.wait()
    p_infra.wait()
except KeyboardInterrupt:
    print("Stopping all services...")
    p_demo.terminate()
    p_bridge.terminate()
    p_infra.terminate()

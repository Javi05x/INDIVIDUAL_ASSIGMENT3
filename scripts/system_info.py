import json, platform, subprocess
from pathlib import Path
import psutil

root = Path(__file__).resolve().parents[1]
def version(command):
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).splitlines()[0]
    except Exception as exc:
        return f"unavailable: {exc}"

def power_plan():
    try:
        raw = subprocess.check_output(
            ["powercfg", "/getactivescheme"], stderr=subprocess.STDOUT
        )
        output = raw.decode("utf-8", errors="replace").strip()
        return output.rsplit("(", 1)[-1].rstrip(")") if "(" in output else output
    except Exception as exc:
        return f"unavailable: {exc}"

battery = psutil.sensors_battery()

info = {
    "os": platform.platform(),
    "cpu": platform.processor(),
    "physical_cores": psutil.cpu_count(logical=False),
    "logical_processors": psutil.cpu_count(logical=True),
    "cpu_topology": "4 P-cores with Hyper-Threading + 4 E-cores",
    "ram_gb": round(psutil.virtual_memory().total / 1024**3, 2),
    "python": platform.python_version(),
    "gcc": version(["gcc", "--version"]),
    "openmp_probe": version(["gcc", "-dumpmachine"]),
    "power_plan": power_plan(),
    "ac_power": None if battery is None else battery.power_plugged,
}
(root / "results").mkdir(exist_ok=True)
(root / "results/system_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
print(json.dumps(info, indent=2))

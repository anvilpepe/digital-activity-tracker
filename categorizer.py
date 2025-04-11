import time
import psutil
import win32gui
import win32process
import json
from jsonschema import validate
schema = {
    "type": "object",
    "properties": {
        "process_rules": {"type": "object"},
        "window_rules": {"type": "object"},
        "browser_specific": {"type": "object"},
        # "blocklist": {"type": "array"},
        "pomodoro": {"type": "object"}
    },
    "required": ["process_rules", "window_rules"]
}
default_cfg = {
  "process_rules": {
    "Telegram.exe": "Соцсети",
    "Discord.exe": "Соцсети",
    "pycharm64.exe": "Разработка",
    "python3.12.exe": "Разработка",
    "vscode.exe": "Разработка"
  },
  "window_restrictions": {
    "YouTube":
    {
      "max_minutes_per_day": 3600
    }
  },
  "window_rules": {
    "Работа": ["Jira", "Confluence", "GitHub", "python3"],
    "Развлечения": ["YouTube", "Twitch", "Steam"]
  },
  "blocklist": {
    "categories": [],
    "processes": [],
    "apps": []
  },
  "title_overrides":{
    "pycharm64": "PyCharm",
    "Taskmgr": "Диспетчер задач",
    "wps": "WPS Office",
    "firefox": "Mozilla Firefox",
    "explorer": "Проводник"
  }
}
pomodoro_default = """
"pomodoro": {
    "work_minutes": 25,
    "break_minutes": 5
  },
"""

def load_config(path="config.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        with open(path, "w+", encoding="utf-8") as f:
            f.write(default_cfg)
        return  load_config()
def get_pomodoro(cfg_json=load_config()) -> None | dict:
    pomodoro_cfg = cfg_json.get("pomodoro", None)
    if not pomodoro_cfg:
        return None
    return {"work_minutes": pomodoro_cfg.get("work_minutes", 25),
            "break_minutes": pomodoro_cfg.get("break_minutes", 5)}


class ProcessInfo:
    def __init__(self, pid, process_name, exe_path):
        self.pid = pid
        self.process_name : str = process_name
        self.exe_path = exe_path

    def __str__(self):
        return f"Process {self.process_name} ({self.exe_path}) ({self.pid})"
class WindowInfo:
    def __init__(self, title : str = "Unknown", process_info : ProcessInfo = ProcessInfo(-1, "unk", "unk")):
        self.title = title
        self.info = process_info

    def __str__(self):
        return f"{self.title} : {self.info}"
class Category:
    def __init__(self, name : str, display_title : str, raw_title : str, window: WindowInfo = None):
        self.name = name
        self.raw_title = raw_title
        self.display_title = display_title
        self.window = window
    def __str__(self):
        return f"{self.display_title} : {self.name}"

def try_get_active_window_properties() -> None | WindowInfo:
    # window = pgw.getActiveWindow()
    window = win32gui.GetForegroundWindow()
    if not window: return None
    try:
        _,pid = win32process.GetWindowThreadProcessId(window)
        process = psutil.Process(pid)
        process_name = process.name()
        exe_path = process.exe()
        result = WindowInfo(win32gui.GetWindowText(window), ProcessInfo(pid, process_name, exe_path))
    except Exception as e:
        result = None
        print(f"Failed to resolve window's properties: {e}")

    return result

def categorize(window : WindowInfo) -> Category:
    if not window: raise Exception("Passed None as a window")
    if window.info.pid == -1: raise Exception(f"Invalid process info for {window}")
    cfg = load_config()

    category = cfg["process_rules"].get(window.info.process_name, None)
    kw_title : str = ""
    do_from_title = False
    if not category:
        for cat, kws in cfg["window_rules"].items():
            if any(kw in window.title for kw in kws):
                category = cat
                for kw in kws:
                    if kw in window.title:
                        kw_title = kw
                do_from_title = True
                break
        else:
            category = "Другое"
    raw_title = window.info.process_name.removesuffix(".exe") if not do_from_title else kw_title
    return Category(
        name = category,
        display_title=cfg.get("title_overrides", raw_title).get(raw_title, raw_title),
        raw_title=window.info.process_name.removesuffix(".exe"),
        window=window
    )


if __name__ == "__main__":
    print("Categorizer testing started.")
    print("waiting for 3..."); time.sleep(3)
    win_props = try_get_active_window_properties()
    print(win_props)
    print(categorize(win_props))
    print("Categorizer testing ended.")

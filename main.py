import time
import sqlite3
import psutil
from datetime import datetime
import categorizer
from categorizer import try_get_active_window_properties as tgw, categorize, Category
# from win10toast import ToastNotifier

productivity_keywords = ["PyCharm", "Visual Studio Code", ".py"]
distraction_keywords = ["YouTube", "Reddit", "Telegram"]
cfg = categorizer.load_config()
# toast = ToastNotifier()

def get_db_connection():
    con = sqlite3.connect("track.db", check_same_thread=False)

    con.cursor().execute("""
            CREATE TABLE IF NOT EXISTS track(
                title TEXT PRIMARY KEY,
                process_name TEXT,
                category TEXT,
                seconds INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
            """)

    return con

def handle_restrictions(category : Category):
    con = get_db_connection()
    cur = con.cursor()
    kill = psutil.Process(category.window.info.pid).kill

    timestamp = cur.execute("SELECT last_updated FROM track WHERE title=?", (category.display_title,)).fetchone()
    timestamp = timestamp[0] if timestamp else None
    seconds = cur.execute("SELECT seconds FROM track WHERE title=?", (category.display_title,)).fetchone()
    seconds = seconds[0] if seconds else None
    if not seconds: return
    now, ts_mon, ts_day = 0,0,0
    if timestamp:
        now = datetime.now()
        ts_sep = str(timestamp).split('-')
        ts_mon = int(ts_sep[1])
        ts_day = ts_sep[2]
        ts_day = int(ts_day[:2])
        # print((now.month, now.day) == (ts_mon, ts_day))
    else: return

    if cfg.get("window_restrictions", None):
        for name, params in cfg["window_restrictions"].items():
            if not name in category.display_title or not (ts_mon, ts_day) == (now.month, now.day): continue
            always = params.get("always_blocked", False)
            if always: kill()
            mins = params.get("max_minutes_per_day", None)
            if not mins: continue
            if seconds / 60 > mins: kill()


    blocklist = cfg.get("blocklist", None)
    if not blocklist: return
    categories = blocklist.get("categories", None)
    processes = blocklist.get("processes", None)
    apps = blocklist.get("apps", None)
    if categories:
        for cat in categories:
            if cat == category.name: kill()
    if processes:
        for p in processes:
            if p == category.window.info.process_name: kill()
    if apps:
        for app in apps:
            if app in category.display_title: kill()

def main():
    con = get_db_connection()
    cur = con.cursor()

    pomodoro = categorizer.get_pomodoro()
    working_for = 0
    working = True
    resting_for = 0

    try:
        while True:
            window = tgw()
            if not window:
                time.sleep(1)
                continue

            category = categorize(window)
            handle_restrictions(category)
            with con:
                cur.execute("SELECT seconds FROM track WHERE title=?", (category.display_title,))
                cur_seconds = cur.fetchone()
                cur_seconds = cur_seconds[0] if cur_seconds else 0
                cur.execute("""
                    INSERT OR REPLACE INTO track VALUES(?,?,?,?,CURRENT_TIMESTAMP) 
                    """,
        (category.display_title, category.raw_title, category.name, cur_seconds + 1))
                con.commit()


                time.sleep(1)

    except KeyboardInterrupt:
        con.close()
        print("Database connection closed")

if __name__ == "__main__":
    main()
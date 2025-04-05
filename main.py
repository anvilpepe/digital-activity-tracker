import time
import sqlite3
import psutil
from datetime import datetime

import categorizer
from categorizer import try_get_active_window_properties as tgw, categorize, Category

productivity_keywords = ["PyCharm", "Visual Studio Code", ".py"]
distraction_keywords = ["YouTube", "Reddit", "Telegram"]


def get_db_connection():
    return sqlite3.connect("track.db", check_same_thread=False)


def main():
    con = get_db_connection()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS track(
            title TEXT PRIMARY KEY,
            process_name TEXT,
            category TEXT,
            seconds INTEGER)
        """)

    pomodoro = categorizer.get_pomodoro()
    working_for = 0
    resting_for = 0

    try:
        while True:
            window = tgw()
            if not window:
                time.sleep(1)
                continue

            category = categorize(window)

            with con:
                cur.execute("SELECT seconds FROM track WHERE title=?", (category.display_title,))
                cur_seconds = cur.fetchone()
                cur_seconds = cur_seconds[0] if cur_seconds else 0
                cur.execute("INSERT OR REPLACE INTO track VALUES(?,?,?,?)",
                            (category.display_title, category.raw_title, category.name, cur_seconds + 1))
                con.commit()
                time.sleep(1)

    except KeyboardInterrupt:
        con.close()
        print("Database connection closed")

if __name__ == "__main__":
    main()
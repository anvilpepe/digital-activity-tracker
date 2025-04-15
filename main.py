import psutil, json, sqlite3, time
from datetime import datetime, date
from win10toast import ToastNotifier
import categorizer
from categorizer import try_get_active_window_properties as tgw, categorize, Category

def get_db_connection():
    con = sqlite3.connect("track.db", check_same_thread=False)

    con.cursor().execute("""
        CREATE TABLE IF NOT EXISTS track(
            title TEXT,
            process_name TEXT,
            category TEXT,
            seconds INTEGER,
            date DATE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (title, date))
        """)

    return con

cfg : dict = categorizer.load_config()

def handle_restrictions(category: Category):
    con = get_db_connection()
    cur = con.cursor()
    kill = psutil.Process(category.window.info.pid).kill
    today = date.today().isoformat()

    # Получаем статистику за текущий день
    cur.execute("""
        SELECT SUM(seconds) 
        FROM track 
        WHERE title = ? AND date = ?
    """, (category.display_title, today))

    total_seconds = cur.fetchone()[0] or 0

    if cfg.get("window_restrictions", None):
        for name, params in cfg["window_restrictions"].items():
            if name not in category.display_title:
                continue

            # Проверка дневного лимита
            mins = params.get("max_minutes_per_day", None)
            if mins and (total_seconds / 60) > mins:
                kill()

            # Мгновенная блокировка
            if params.get("always_blocked", False):
                kill()

    blocklist : dict | None = cfg.get("blocklist", None)
    if blocklist:
        categories = blocklist.get("categories", [])
        processes = blocklist.get("processes", [])
        apps = blocklist.get("apps", [])

        if category.name in categories:
            kill()
        if category.window.info.process_name in processes:
            kill()
        if any(app in category.display_title for app in apps):
            kill()


def main():
    con = get_db_connection()
    cur = con.cursor()
    today = date.today().isoformat()


    try:
        while True:
            window = tgw()
            if not window:
                time.sleep(1)
                continue

            category = categorize(window)
            handle_restrictions(category)

            with con:
                # Обновляем или создаем запись для текущего дня
                cur.execute("""
                    INSERT INTO track (title, process_name, category, seconds, date)
                    VALUES (?, ?, ?, 1, ?)
                    ON CONFLICT(title, date) DO UPDATE SET
                        seconds = seconds + 1,
                        last_updated = CURRENT_TIMESTAMP
                """, (category.display_title, category.raw_title, category.name, today))

                con.commit()

            # notifier.check_notifications()
            time.sleep(1)

    except KeyboardInterrupt:
        con.close()
        print("Database connection closed")

def insert_debug_entry(title: str, process_name: str, category: str,
                       seconds: int, target_date: str):
    """
    Вставляет тестовую запись с указанной датой
    Пример использования:
    insert_debug_entry("Chrome", "chrome.exe", "Работа", 3600, "2024-04-01")
    """
    try:
        # Проверяем формат даты
        datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        print("Некорректный формат даты. Используйте YYYY-MM-DD")
        return

    con = get_db_connection()
    cur = con.cursor()

    try:
        cur.execute("""
            INSERT INTO track (title, process_name, category, seconds, date)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(title, date) DO UPDATE SET
                seconds = excluded.seconds,
                last_updated = CURRENT_TIMESTAMP
        """, (title, process_name, category, seconds, target_date))

        con.commit()
        print(f"Успешно добавлена запись за {target_date}")

    except Exception as e:
        print(f"Ошибка при вставке: {str(e)}")
    finally:
        con.close()

if __name__ == "__main__":
    # insert_debug_entry(
    #     title="AAAAAAAAAAA",
    #     category="a",
    #     target_date="1980-01-01",
    #     seconds=9999,
    #     process_name="sasdoas"
    # )
    main()



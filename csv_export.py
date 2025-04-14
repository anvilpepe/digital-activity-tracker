import csv
import os
import sqlite3 as sql

def export(path_to_db: str = "track.db", table_name="track", export_path: str = "export.csv", where_clause : str = "", params = ()) -> str | None:
    try:
        con = sql.connect(path_to_db)
        cur = con.cursor()

        cur.execute(f"SELECT * FROM {table_name} {where_clause}", params)
        rows = cur.fetchall()

        if not os.path.isdir(os.getcwd() + "\\export"):
            os.mkdir(os.getcwd() + "\\export")

        with open("export/"+export_path, "w+", encoding="utf-16", newline='') as f:
            csv_w = csv.writer(f, delimiter='\t')
            csv_w.writerow([i[0] for i in cur.description])
            csv_w.writerows(rows)

        dirpath = os.getcwd() + export_path
        return f"Данные успешно экспортированы в {export_path}"
    except Exception as e:
        return f"Не удалось экспортировать данные: {e}"

if __name__ == "__main__":
    print("Export testing started.")
    print(export())
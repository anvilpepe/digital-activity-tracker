import tkinter as tk
from tkinter import ttk
import sqlite3
import threading
import categorizer
import main

class ActivityTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Digital Activity Tracker")
        self.geometry("800x400")
        self.db_conn = sqlite3.connect("track.db", check_same_thread=False)
        self.setup_ui()
        self.update_data()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    def setup_ui(self):
        control_frame = ttk.Frame(self)
        control_frame.pack(pady=10, fill=tk.X)

        self.current_activity = ttk.Label(
            self,
            text="Current activity: Not detected",
            font=('Helvetica', 12)
        )
        self.current_activity.pack(pady=5, anchor=tk.W, padx=10)

        columns = ('title', 'category', 'seconds')
        self.stats_tree = ttk.Treeview(
            self,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        self.stats_tree.heading('title', text='Application')
        self.stats_tree.heading('category', text='Category')
        self.stats_tree.heading('seconds', text='Time (sec)')

        self.stats_tree.column('title', width=300)
        self.stats_tree.column('category', width=200)
        self.stats_tree.column('seconds', width=100)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.stats_tree.yview)
        self.stats_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_tree.pack(fill=tk.BOTH, expand=True, padx=10)

    def update_data(self):
        try:
            cur = self.db_conn.cursor()
            stats = cur.execute("""
                SELECT 
                    title,
                    category,
                    seconds
                FROM track
                ORDER BY seconds DESC
            """).fetchall()
            self.current_activity.config(text=f"Current activity: {categorizer.categorize(main.tgw()).display_title}")

            # Очистка и обновление Treeview
            self.stats_tree.delete(*self.stats_tree.get_children())
            for row in stats:
                self.stats_tree.insert('', 'end', values=row)

        finally:
            self.after(1000, self.update_data)

    def on_close(self):
        self.db_conn.close()
        self.destroy()


def run_tracker():
    from main import main
    main()


if __name__ == "__main__":
    app = ActivityTrackerApp()
    tracker_thread = threading.Thread(target=run_tracker, daemon=True)
    tracker_thread.start()
    app.mainloop()
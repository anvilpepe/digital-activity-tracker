import tkinter as tk
from tkinter import ttk
import sqlite3
import threading
import categorizer
import main
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


class ActivityTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Digital Activity Tracker")
        self.geometry("1200x800")
        self.db_conn = main.get_db_connection()
        self.charts_visible = True
        self.setup_ui()
        self.update_data()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # Основной контейнер
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Панель управления
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        # Кнопка управления графиками
        self.toggle_btn = ttk.Button(
            control_frame,
            text="Скрыть графики",
            command=self.toggle_charts
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=5)

        # Левая панель - таблица
        self.left_panel = ttk.Frame(main_frame)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Правая панель - графики
        self.right_panel = ttk.Frame(main_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Таблица статистики
        self.setup_table()

        # Графики
        self.setup_charts()

    def setup_table(self):
        columns = ('title', 'category', 'seconds')
        self.stats_tree = ttk.Treeview(
            self.left_panel,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        self.stats_tree.heading('title', text='Application')
        self.stats_tree.heading('category', text='Category')
        self.stats_tree.heading('seconds', text='Time (sec)')

        scrollbar = ttk.Scrollbar(self.left_panel, orient=tk.VERTICAL, command=self.stats_tree.yview)
        self.stats_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_tree.pack(fill=tk.BOTH, expand=True)

    def setup_charts(self):
        # Контейнер для графиков
        self.chart_container = ttk.Frame(self.right_panel)
        self.chart_container.pack(fill=tk.BOTH, expand=True, pady=10)

        # Диаграмма по категориям
        self.category_fig, self.category_ax = plt.subplots(figsize=(1, 1))
        self.category_canvas = FigureCanvasTkAgg(self.category_fig, master=self.chart_container)
        self.category_widget = self.category_canvas.get_tk_widget()
        self.category_widget.pack(fill=tk.BOTH, expand=True)

        # Диаграмма по приложениям
        self.apps_fig, self.apps_ax = plt.subplots(figsize=(1, 1))
        self.apps_canvas = FigureCanvasTkAgg(self.apps_fig, master=self.chart_container)
        self.apps_widget = self.apps_canvas.get_tk_widget()
        self.apps_widget.pack(fill=tk.BOTH, expand=True)

    def toggle_charts(self):
        self.charts_visible = not self.charts_visible
        if self.charts_visible:
            self.chart_container.pack(fill=tk.BOTH, expand=True, pady=10)
            self.toggle_btn.config(text="Скрыть графики")
        else:
            self.chart_container.pack_forget()
            self.toggle_btn.config(text="Показать графики")

    def update_charts(self, category_data, app_data):
        # Очищаем предыдущие графики
        self.category_ax.clear()
        self.apps_ax.clear()

        # Общие настройки
        legend_params = {
            'loc': 'upper left',
            'bbox_to_anchor': (1, 1),
            'fontsize': 8
        }

        # Диаграмма по категориям
        if category_data:
            labels, sizes = zip(*category_data)
            wedges, _ = self.category_ax.pie(
                sizes,
                startangle=90,
                wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
            )
            self.category_ax.legend(
                wedges,
                labels,
                title="Категории",
                **legend_params
            )
            # self.category_ax.set_title('Распределение по категориям', pad=20)

        # Диаграмма по приложениям
        if app_data:
            labels, sizes = zip(*app_data)
            # print(category_data)
            wedges, _ = self.apps_ax.pie(
                sizes,
                startangle=90,
                wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
            )
            self.apps_ax.legend(
                wedges,
                labels,
                title="Приложения",
                **legend_params
            )
            # self.apps_ax.set_title('Распределение по приложениям', pad=20)

        # Настройка отступов
        self.category_fig.tight_layout(pad=0.2)
        self.apps_fig.tight_layout(pad=0.2)

        # Обновляем canvas
        self.category_canvas.draw()
        self.apps_canvas.draw()

    def update_data(self):
        try:
            cur = self.db_conn.cursor()

            # Получаем данные для категорий
            category_data = cur.execute("""
                SELECT category, SUM(seconds) 
                FROM track 
                GROUP BY category 
                ORDER BY SUM(seconds) DESC
            """).fetchall()

            # Получаем данные для приложений
            app_data = cur.execute("""
                SELECT title, SUM(seconds) 
                FROM track 
                GROUP BY title 
                ORDER BY SUM(seconds) DESC 
                LIMIT 15
            """).fetchall()

            # Обновляем таблицу
            self.stats_tree.delete(*self.stats_tree.get_children())
            for title, category, seconds in cur.execute("""
                SELECT title, category, SUM(seconds) 
                FROM track 
                GROUP BY title 
                ORDER BY SUM(seconds) DESC
            """):
                self.stats_tree.insert('', 'end', values=(title, category, seconds))

            # Обновляем графики
            if self.charts_visible:
                self.update_charts(category_data, app_data)

        finally:
            self.after(5000, self.update_data)

    def on_close(self):
        self.db_conn.close()
        plt.close('all')
        self.destroy()


def run_tracker():
    from main import main
    main()


if __name__ == "__main__":
    app = ActivityTrackerApp()
    tracker_thread = threading.Thread(target=run_tracker, daemon=True)
    tracker_thread.start()
    app.mainloop()
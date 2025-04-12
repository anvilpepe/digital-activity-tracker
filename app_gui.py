import tkinter as tk
from tkinter import ttk
import threading
import csv_export
import main
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
from ttkthemes import ThemedStyle

class ActivityTrackerApp(tk.Tk):
    def __init__(self, username, auth_system):
        super().__init__()
        self.title("Digital Activity Tracker")
        self.geometry("1400x900")
        self.resizable(False, False)
        self.minsize(1200, 800)
        self.auth = auth_system
        self.db_path = self.auth.get_path() + f"\\user_{self.auth.hash(username, bytes.fromhex(self.auth.get_salt(username)))[0]}.db"
        self.db_conn = main.get_db_connection(self.db_path)
        self.theme_mode = "dark"  # Начальная тема
        self.setup_theme()
        self.setup_ui()
        self.update_data()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        tracker_thread = threading.Thread(target=run_tracker(self.db_path), daemon=True)
        tracker_thread.start()
        # self.bind("<Configure>", self.on_window_resize) # doesn't work

    def setup_theme(self):
        self.style = ThemedStyle(self)
        self.style.set_theme("equilux" if self.theme_mode == "dark" else "arc")

        # Настройка цветов для разных тем
        if self.theme_mode == "dark":
            self.bg_color = "#464646"
            self.text_color = "white"
            self.chart_bg = "#2E2E2E"
        else:
            self.bg_color = "#FFFFFF"
            self.text_color = "black"
            self.chart_bg = "#F5F6F7"

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main container
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.grid(row=0, column=0, sticky='nsew')

        # Left panel (Table)
        self.left_panel = ttk.Frame(main_paned)
        main_paned.add(self.left_panel, weight=2)

        # Right panel (Charts)
        self.right_panel = ttk.Frame(main_paned)
        main_paned.add(self.right_panel, weight=3)

        # Control panel
        control_frame = ttk.Frame(self.left_panel)
        control_frame.pack(fill=tk.X, pady=5)

        # Кнопка переключения темы
        self.theme_btn = ttk.Button(
            control_frame,
            text="🌙 Светлая тема" if self.theme_mode == "dark" else "🌞 Тёмная тема",
            command=self.toggle_theme,
            width=15
        )
        self.theme_btn.pack(side=tk.RIGHT, padx=5)

        # Остальные элементы управления...
        self.mode_var = tk.StringVar(value="Общая статистика")
        mode_menu = ttk.Combobox(
            control_frame,
            textvariable=self.mode_var,
            values=["Общая статистика", "Статистика за день", "Статистика за вчера"],
            state="readonly",
            font=('Segoe UI', 10),
            width=20
        )
        mode_menu.pack(side=tk.LEFT, padx=5)
        mode_menu.bind("<<ComboboxSelected>>", lambda e: self.update_data())

        self.toggle_btn = ttk.Button(
            control_frame,
            text="▲ Скрыть графики",
            command=self.toggle_charts
        )
        self.toggle_btn.pack(side=tk.RIGHT, padx=5)

        self.export_btn = ttk.Button(
            control_frame,
            text="Экспорт",
            command=self.export_to_csv
        )
        self.export_btn.pack(side=tk.RIGHT, padx=5)

        # Таблица и графики...
        self.setup_table()
        self.setup_charts()

        # Status bar
        self.status_bar = ttk.Label(self, text="Готово", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky='ew')

    @staticmethod
    def export_to_csv(self):
        messagebox.showinfo(title='Результат', message=csv_export.export())

    def toggle_theme(self):
        # Переключение между темами
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.setup_theme()
        self.theme_btn.config(
            text="🌞 Тёмная тема" if self.theme_mode == "light" else "🌙 Светлая тема"
        )

        # Обновление цветов графиков
        self.update_chart_colors()

        # Обновление стилей виджетов
        self.update_widget_styles()
        self.status_bar.config(text=f"Тема изменена на {'светлую' if self.theme_mode == 'light' else 'тёмную'}")

    def update_chart_colors(self):
        # Обновление цветов графиков
        for fig, ax in [(self.category_fig, self.category_ax),
                        (self.apps_fig, self.apps_ax)]:
            fig.patch.set_facecolor(self.bg_color)
            ax.set_facecolor(self.bg_color)

            for text in ax.texts:
                text.set_color(self.text_color)

            if ax.title.get_text():
                ax.title.set_color(self.text_color)

            if ax.get_legend():
                ax.get_legend().get_title().set_color(self.text_color)
                for text in ax.get_legend().get_texts():
                    text.set_color(self.text_color)

        self.category_canvas.draw_idle()
        self.apps_canvas.draw_idle()

    def update_widget_styles(self):
        # Обновление стилей для виджетов
        self.style.configure(
            "Treeview",
            background=self.bg_color,
            fieldbackground=self.bg_color,
            foreground=self.text_color
        )

        self.style.configure(
            "Treeview.Heading",
            background=self.chart_bg,
            foreground=self.text_color,
            font=('Segoe UI', 10, 'bold')
        )

        self.style.map(
            "Treeview",
            background=[('selected', '#3B8ED0' if self.theme_mode == 'dark' else '#1E90FF')]
        )

    def setup_table(self):
        columns = ('title', 'category', 'seconds', 'percentage')
        self.stats_tree = ttk.Treeview(
            self.left_panel,
            columns=columns,
            show='headings',
            selectmode='browse',
            style="Custom.Treeview"
        )

        # Configure columns
        self.stats_tree.heading('title', text='Приложение', command=lambda: self.sort_column('title', False))
        self.stats_tree.heading('category', text='Категория', command=lambda: self.sort_column('category', False))
        self.stats_tree.heading('seconds', text='Время', command=lambda: self.sort_column('seconds', False))
        self.stats_tree.heading('percentage', text='Процент', command=lambda : self.sort_column('percentage', False))

        self.stats_tree.column('title', width=200, anchor=tk.W)
        self.stats_tree.column('category', width=150, anchor=tk.W)
        self.stats_tree.column('seconds', width=75, anchor=tk.E)
        self.stats_tree.column('percentage', width=70, anchor=tk.E)

        scroll_y = ttk.Scrollbar(self.left_panel, orient=tk.VERTICAL, command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_tree.pack(fill=tk.BOTH, expand=True)

    def sort_column(self, col, reverse):
        data = [(self.stats_tree.set(child, col), child) for child in self.stats_tree.get_children('')]
        data.sort(reverse=reverse, key=lambda x: x[0].lower() if col != 'seconds' else float(x[0]))

        for index, (val, child) in enumerate(data):
            self.stats_tree.move(child, '', index)
            tag = 'even' if index % 2 == 0 else 'odd'
            self.stats_tree.item(child, tags=(tag,))

        self.stats_tree.heading(col, command=lambda: self.sort_column(col, not reverse))

    def setup_charts(self):
        self.chart_container = ttk.Frame(self.right_panel)
        self.chart_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Category chart
        self.category_fig, self.category_ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.category_fig.patch.set_facecolor(self.bg_color)
        self.category_canvas = FigureCanvasTkAgg(self.category_fig, self.chart_container)
        self.category_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=5)

        # App chart
        self.apps_fig, self.apps_ax = plt.subplots(figsize=(8, 4), dpi=100)
        self.apps_fig.patch.set_facecolor(self.bg_color)
        self.apps_canvas = FigureCanvasTkAgg(self.apps_fig, self.chart_container)
        self.apps_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=5)

    def update_charts(self, category_data, app_data):
        # Очистка предыдущих графиков
        self.category_ax.clear()
        self.apps_ax.clear()

        # Установка цветов в соответствии с темой
        colors = plt.cm.tab20.colors
        self.category_ax.set_facecolor(self.bg_color)
        self.apps_ax.set_facecolor(self.bg_color)

        legend_params = {
            'loc': 'upper left',
            'bbox_to_anchor': (0, 1),
            'fontsize': 8
        }

        if category_data:
            labels, sizes = zip(*category_data)
            total = sum(sizes)
            percentages = [f'{(s / total) * 100:.1f}%' for s in sizes]

            wedges, texts = self.category_ax.pie(
                sizes,
                # labels=percentages, # мне не нужно это на графике
                colors=colors,
                startangle=140,
                wedgeprops={'linewidth': 1.5, 'edgecolor': 'w'},
                pctdistance=0.85,
                textprops={'color': self.text_color, 'fontsize': 9}
            )

            self.category_ax.axis('equal')
            self.category_ax.set_title('Распределение по категориям',
                                       color=self.text_color, pad=20)

            self.category_ax.legend(
                wedges,
                labels,
                title="Категории",
                **legend_params
            )

        if app_data:
            labels, sizes = zip(*app_data)
            bars = self.apps_ax.barh(labels, sizes, color=colors)
            self.apps_ax.bar_label(bars, padding=5, color=self.text_color, fmt='%d сек')
            self.apps_ax.tick_params(axis='both', colors=self.text_color)
            self.apps_ax.set_title('Топ приложений', color=self.text_color, pad=15)

        # Обновление canvas
        self.category_canvas.draw()
        self.apps_canvas.draw()

    def toggle_charts(self):
        if self.chart_container.winfo_ismapped():
            self.chart_container.pack_forget()
            self.toggle_btn.config(text="▼ Показать графики")
        else:
            self.chart_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.toggle_btn.config(text="▲ Скрыть графики")

    def update_data(self):
        try:
            cur = self.db_conn.cursor()
            today = datetime.now().date().isoformat()
            yesterday = (datetime.now() - timedelta(1)).strftime("%Y-%m-%d")
            mode = self.mode_var.get()

            # Базовые условия для запросов
            where_clause = "WHERE date = ?" if mode == "Статистика за день" or mode == "Статистика за вчера" else ""
            params = (today,) if mode == "Статистика за день" else (yesterday,) if mode == "Статистика за вчера" else ()

            # Получаем данные для категорий
            category_query = f"""
                SELECT category, SUM(seconds) 
                FROM track 
                {where_clause}
                GROUP BY category 
                ORDER BY SUM(seconds) DESC
            """
            category_data = cur.execute(category_query, params).fetchall()

            # Получаем данные для приложений
            app_query = f"""
                SELECT title, SUM(seconds) 
                FROM track 
                {where_clause}
                GROUP BY title 
                ORDER BY SUM(seconds) DESC 
                LIMIT 10
            """
            app_data = cur.execute(app_query, params).fetchall()

            # Обновляем таблицу
            self.stats_tree.delete(*self.stats_tree.get_children())
            table_query = f"""
                SELECT title, category, SUM(seconds) 
                FROM track 
                {where_clause}
                GROUP BY title 
                ORDER BY SUM(seconds) DESC
            """
            total_time_query = f"""
                SELECT SUM(seconds)
                FROM track
                {where_clause}
            """

            total_time = cur.execute(total_time_query, params).fetchone()

            # print(total_time)
            for row in cur.execute(table_query, params):
                percent = tuple([round(100 * row[2] / total_time[0] if total_time else 1, 2)])
                self.stats_tree.insert('', 'end', values=row + percent)

            # Обновляем графики

            self.update_charts(category_data, app_data)

            self.status_bar.config(text=f"Данные обновлены: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            # raise e
            messagebox.showerror("Ошибка", f"Ошибка обновления данных: {str(e)}")
        finally:
            self.after(5000, self.update_data)
    def on_close(self):
        self.db_conn.close()
        plt.close('all')
        self.destroy()


def run_tracker(db_path="track.db"):
    from main import main
    main(db_path)

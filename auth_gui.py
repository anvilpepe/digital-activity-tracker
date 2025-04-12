import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
from app_gui import ActivityTrackerApp
from auth import AuthSystem

class AuthWindow(tk.Tk):
    def __init__(self, auth_system):
        super().__init__()
        self.auth = auth_system
        self.title("Вход")
        self.geometry("225x150")
        self.resizable(False, False)

        self.remember = IntVar()
        self.create_widgets()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Логин:").grid(row=0, column=0, sticky=tk.W)
        self.username_entry = ttk.Entry(main_frame)
        self.username_entry.grid(row=0, column=1, pady=5)

        ttk.Label(main_frame, text="Пароль:").grid(row=1, column=0, sticky=tk.W)
        self.password_entry = ttk.Entry(main_frame, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        # checkbox_frame = ttk.Frame(main_frame)
        # checkbox_frame.grid(row=2, column=0, columnspan=2, pady=0)
        # self.remember_checkbox = ttk.Checkbutton(
        #     checkbox_frame,
        #     text="Больше не спрашивать",
        #     variable=self.remember
        # )
        # self.remember_checkbox.pack(side=tk.TOP, pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=6)

        ttk.Button(
            btn_frame,
            text="Войти",
            command=self.login
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Регистрация",
            command=self.register
        ).pack(side=tk.LEFT, padx=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return

        if self.auth.verify_user(username, password):
            self.destroy()
            ActivityTrackerApp(username, auth_system=self.auth).mainloop()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")

    def register(self):
        RegisterWindow(self.auth, self)


class RegisterWindow(tk.Toplevel):
    def __init__(self, auth_system, parent):
        super().__init__(parent)
        self.auth = auth_system
        self.parent = parent
        self.title("Регистрация")
        self.geometry("225x150")
        self.resizable(False, False)

        self.create_widgets()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Логин:").grid(row=0, column=0, sticky=tk.W)
        self.username_entry = ttk.Entry(main_frame)
        self.username_entry.grid(row=0, column=1, pady=5)

        ttk.Label(main_frame, text="Пароль:").grid(row=1, column=0, sticky=tk.W)
        self.password_entry = ttk.Entry(main_frame, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        ttk.Button(
            main_frame,
            text="Зарегистрироваться",
            command=self.register
        ).grid(row=2, column=0, columnspan=2, pady=10)

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return

        if self.auth.register_user(username, password):
            messagebox.showinfo("Успех", "Регистрация прошла успешно!")
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Пользователь уже существует")

if __name__ == "__main__":
    auth = AuthSystem()
    app = AuthWindow(auth)
    app.mainloop()
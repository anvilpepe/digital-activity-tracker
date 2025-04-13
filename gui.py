from auth_gui import AuthWindow
from auth import AuthSystem

if __name__ == "__main__":
    app = AuthWindow(AuthSystem())

    app.mainloop()
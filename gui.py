import auth_gui
from auth import AuthSystem

if __name__ == "__main__":
    app = auth_gui.AuthWindow(AuthSystem())
    app.mainloop()
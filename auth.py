import os
import hashlib
import sqlite3 as sql

AUTH_DB_FILENAME = "auth.db"

def is_first_launch():
    return not os.path.isfile(AuthSystem.get_path() + f"\\{AUTH_DB_FILENAME}")

class AuthSystem:
    def __init__(self):
        self.db_con = sql.connect(self.get_auth_db_path(), check_same_thread=False)
        self.db_cur = self.db_con.cursor()

        self.db_cur.execute("""
            CREATE TABLE IF NOT EXISTS users(
                name TEXT PRIMARY KEY,
                hashed_password TEXT,
                salt TEXT
            )
        """)

    @staticmethod
    def get_path() -> str:
        path = os.path.isdir(os.getenv('LOCALAPPDATA') + r"\Digital Activity Tracker")
        if not path: os.mkdir(os.getenv('LOCALAPPDATA') + r"\Digital Activity Tracker")
        path = os.getenv('LOCALAPPDATA') + r"\Digital Activity Tracker"
        return path

    @staticmethod
    def get_auth_db_path() -> str:
        return AuthSystem.get_path() + f"\\{AUTH_DB_FILENAME}"

    @staticmethod
    def hash(password, salt=None):
        salt = salt or os.urandom(32)
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            10000
        ).hex(), salt.hex()

    def get_salt(self, username):
        self.db_cur.execute("""
            SELECT salt FROM users WHERE name=?
        """, (username,))
        salt = self.db_cur.fetchone()
        if not salt: return None
        return salt[0]

    def register_user(self, username, password):
        self.db_cur.execute("""
            SELECT * FROM users WHERE name=?    
        """, (username,))
        registered = self.db_cur.fetchone()
        if registered: return False

        hashed_pw, salt = self.hash(password)
        self.db_cur.execute("""
            INSERT INTO users VALUES(?,?,?)
        """, (username, hashed_pw, salt))
        self.db_con.commit()
        return True

    def verify_user(self, username, password):
        self.db_cur.execute("""
            SELECT hashed_password, salt 
            FROM users 
            WHERE name=?
        """, (username,))
        user = self.db_cur.fetchone()
        if not user: return False
        hashed_pw, _ = self.hash(password, bytes.fromhex(user[1]))
        return hashed_pw == user[0]

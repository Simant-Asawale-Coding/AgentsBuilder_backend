import pyodbc
import bcrypt
from app.utils.configuration.appsettings import AppSettings


import uuid

class AuthService:
    def __init__(self):
        settings = AppSettings()
        self.user_table = settings.agentsbuilder_user_table_name
        self.connection_string = settings.agentsbuilder_mssqlconnectionstring

    def get_connection(self):
        # conn_str = (
        #     f"DRIVER={self.driver};"
        #     f"SERVER={self.server},{self.port};"
        #     f"DATABASE={self.database};"
        #     f"UID={self.username};"
        #     f"PWD={self.password}"
        # )
        print(self.connection_string)
        return pyodbc.connect(self.connection_string)

    def sign_up(self, username: str, password_plain: str):
        """
        Registers a new user. Returns user_id (UUID) if successful, None if username already exists.
        Password is securely hashed.
        """
        password_hash = bcrypt.hashpw(password_plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_id = str(uuid.uuid4())
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Check if username already exists
            cursor.execute(f"SELECT 1 FROM {self.user_table} WHERE username = ?", (username,))
            if cursor.fetchone():
                return None  # Username already exists
            cursor.execute(
                f"INSERT INTO {self.user_table} (user_id, username, password_hash) VALUES (?, ?, ?)",
                (user_id, username, password_hash)
            )
            conn.commit()
            return user_id
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass

    def login(self, username: str, password_plain: str):
        """
        Authenticates a user. Returns user_id (UUID) if credentials are correct, None otherwise.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT user_id, password_hash FROM {self.user_table} WHERE username = ?", (username,))
            row = cursor.fetchone()
            if not row:
                return None
            user_id, password_hash = row
            if bcrypt.checkpw(password_plain.encode('utf-8'), password_hash.encode('utf-8')):
                return user_id
            else:
                return None
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass

if __name__ == "__main__":
    auth_service = AuthService()
    print("Auth module test mode.\n1. Sign Up\n2. Login\n")
    action = input("Choose action (1=Sign Up, 2=Login): ").strip()
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    if action == "1":
        user_id = auth_service.sign_up(username, password)
        if user_id:
            print(f"User '{username}' registered successfully. user_id: {user_id}")
        else:
            print(f"Username '{username}' already exists. Registration failed.")
    elif action == "2":
        user_id = auth_service.login(username, password)
        if user_id:
            print(f"Login successful! user_id: {user_id}")
        else:
            print("Invalid credentials.")
    else:
        print("Invalid action.")

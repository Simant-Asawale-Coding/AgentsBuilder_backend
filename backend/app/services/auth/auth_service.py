import os
import pyodbc
import bcrypt
import random
import string
import time
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_CONNECTION_STRING = os.getenv('Database_Connection_String')

# SMTP configuration
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_SENDER = os.getenv('SMTP_SENDER')

OTP_EXPIRY_SECONDS = 300  # 5 minutes

class AuthService:
    def __init__(self):
        self.conn_str = DB_CONNECTION_STRING

    def _get_conn(self):
        return pyodbc.connect(self.conn_str)

    def signup_user(self, full_name, email, password, company_name=None):
        # Check if already pending or in DB
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            # Check if already in users
            cursor.execute("SELECT user_id FROM users WHERE email=?", (email,))
            if cursor.fetchone():
                return False, 'Email already registered.'
            # Check if already pending
            cursor.execute("SELECT email FROM pending_signups WHERE email=?", (email,))
            if cursor.fetchone():
                return False, 'Signup already initiated. Please verify OTP.'
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        otp = ''.join(random.choices(string.digits, k=6))
        expiry = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + OTP_EXPIRY_SECONDS))
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO pending_signups (email, full_name, password_hash, company_name, otp, expiry)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (email, full_name, password_hash, company_name, otp, expiry)
            )
            conn.commit()
        except pyodbc.IntegrityError:
            return False, 'Signup already initiated. Please verify OTP.'
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass
        # Send OTP via email
        subject = "Your OTP for AgentsBuilder Signup"
        body = f"Your OTP for completing signup is: {otp}\nThis code will expire in 5 minutes."
        try:
            self.send_email(email, subject, body)
        except Exception as e:
            return False, f'Failed to send OTP email: {str(e)}'
        return True, 'OTP sent to your email. Please verify to complete signup.'

    def send_email(self, to_email, subject, body):
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SMTP_SENDER
        msg['To'] = to_email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_SENDER, [to_email], msg.as_string())

    def verify_signup_otp(self, email, otp):
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT full_name, password_hash, company_name, otp, expiry FROM pending_signups WHERE email=?",
                (email,)
            )
            row = cursor.fetchone()
            if not row:
                return False, 'No signup pending for this email.'
            full_name, password_hash, company_name, stored_otp, expiry = row
            # Check expiry
            expiry_ts = expiry.timestamp() if hasattr(expiry, 'timestamp') else time.mktime(expiry.timetuple())
            if time.time() > expiry_ts:
                cursor.execute("DELETE FROM pending_signups WHERE email=?", (email,))
                conn.commit()
                return False, 'OTP expired. Please sign up again.'
            if otp != stored_otp:
                return False, 'Invalid OTP.'
            # Insert user into DB as verified
            cursor.execute(
                """
                INSERT INTO users (full_name, email, password_hash, verification, company_name)
                VALUES (?, ?, ?, 1, ?);
                """,
                (full_name, email, password_hash, company_name)
            )
            # Fetch the new user_id
            cursor.execute("SELECT user_id FROM users WHERE email=?", (email,))
            user_id_row = cursor.fetchone()
            user_id = user_id_row[0] if user_id_row else None
            conn.commit()
            cursor.execute("DELETE FROM pending_signups WHERE email=?", (email,))
            conn.commit()
            return True, {'message': 'Signup complete and verified.', 'user_id': user_id}
        except pyodbc.IntegrityError:
            return False, 'Email already registered.'
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass

    def login_user(self, email, password):
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, password_hash, verification FROM users WHERE email=?",
                (email,)
            )
            row = cursor.fetchone()
            if not row:
                return False, 'User not found'
            user_id, password_hash, verified = row
            if not verified:
                return False, 'Email not verified'
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                return True, {'message': 'Login successful', 'user_id': user_id}
            else:
                return False, 'Incorrect password'
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass

    def initiate_password_reset(self, email):
        # Check if user exists
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE email=? AND deleted IS NULL OR deleted=0", (email,))
            if not cursor.fetchone():
                return False, 'User not found.'
            # Generate OTP
            otp = ''.join(random.choices(string.digits, k=6))
            expiry = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + OTP_EXPIRY_SECONDS))
            # Create table if not exists
            try:
                cursor.execute("""
                    CREATE TABLE password_reset_otps (
                        email NVARCHAR(255) PRIMARY KEY,
                        otp NVARCHAR(10) NOT NULL,
                        expiry DATETIME2 NOT NULL
                    )
                """)
                conn.commit()
            except Exception:
                pass  # Ignore if already exists
            # Upsert OTP
            cursor.execute("DELETE FROM password_reset_otps WHERE email=?", (email,))
            cursor.execute(
                "INSERT INTO password_reset_otps (email, otp, expiry) VALUES (?, ?, ?)",
                (email, otp, expiry)
            )
            conn.commit()
            # Send OTP via email
            subject = "Your OTP for AgentsBuilder Password Reset"
            body = f"Your OTP for password reset is: {otp}\nThis code will expire in 5 minutes."
            try:
                self.send_email(email, subject, body)
            except Exception as e:
                return False, f'Failed to send OTP email: {str(e)}'
            return True, 'Password reset OTP sent to your email.'
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass

    def reset_password(self, email, otp, new_password):
        # Check OTP from password_reset_otps table
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT otp, expiry FROM password_reset_otps WHERE email=?", (email,))
            row = cursor.fetchone()
            if not row:
                return False, 'No password reset requested for this email.'
            stored_otp, expiry = row
            expiry_ts = expiry.timestamp() if hasattr(expiry, 'timestamp') else time.mktime(expiry.timetuple())
            if time.time() > expiry_ts:
                cursor.execute("DELETE FROM password_reset_otps WHERE email=?", (email,))
                conn.commit()
                return False, 'OTP expired. Please request password reset again.'
            if otp != stored_otp:
                return False, 'Invalid OTP.'
            # Update password
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "UPDATE users SET password_hash=? WHERE email=?",
                (password_hash, email)
            )
            conn.commit()
            cursor.execute("DELETE FROM password_reset_otps WHERE email=?", (email,))
            conn.commit()
            return True, 'Password has been reset successfully.'
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass

    def delete_user_account(self, user_id):
        # Delete all associated data in other tables here if needed
        # For now, just flag the user as deleted (do not remove email)
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            # Add a deleted flag to users table if not already present
            # For now, anonymize all fields except email and mark as deleted
            cursor.execute("SELECT email FROM users WHERE user_id=?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return False, 'User not found.'
            email = row[0]
            # Anonymize fields and set deleted flag (add column if needed)
            try:
                cursor.execute("ALTER TABLE users ADD deleted BIT DEFAULT 0")
                conn.commit()
            except Exception:
                pass  # Ignore if already exists
            cursor.execute("""
                UPDATE users SET full_name='DELETED', password_hash='DELETED', verification=0, company_name=NULL, deleted=1 WHERE user_id=?
            """, (user_id,))
            conn.commit()
            return True, f"Account for user_id {user_id} deleted, email retained."
        finally:
            try:
                cursor.close()
                conn.close()
            except:
                pass

# Example usage (remove or adapt for integration with FastAPI/Flask)
if __name__ == "__main__":
    service = AuthService()
    print("Auth module test mode.\n1. Sign Up\n2. Verify Signup OTP\n3. Login\n4. Initiate Password Reset\n5. Reset Password\n6. Delete Account\n")
    action = input("Choose action (1-6): ").strip()
    if action == "1":
        name = input("Full Name: ")
        email = input("Email: ")
        password = input("Password: ")
        company = input("Company (optional): ") or None
        success, msg = service.signup_user(name, email, password, company)
        print(msg)
    elif action == "2":
        email = input("Email: ")
        otp = input("OTP: ")
        success, msg = service.verify_signup_otp(email, otp)
        if success:
            print(f"{msg['message']} Your user_id is: {msg['user_id']}")
        else:
            print(msg)
    elif action == "3":
        email = input("Email: ")
        password = input("Password: ")
        success, msg = service.login_user(email, password)
        if success:
            print(f"{msg['message']} Your user_id is: {msg['user_id']}")
        else:
            print(msg)
    elif action == "4":
        email = input("Email: ")
        print(service.initiate_password_reset(email))
    elif action == "5":
        email = input("Email: ")
        otp = input("OTP: ")
        new_password = input("New Password: ")
        print(service.reset_password(email, otp, new_password))
    elif action == "6":
        email = input("Email: ")
        password = input("Password: ")
        success, msg = service.login_user(email, password)
        if success:
            user_id = msg['user_id']
            confirm = input(f"Are you sure you want to delete account with user_id {user_id}? Type 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                print(service.delete_user_account(user_id))
            else:
                print("Account deletion cancelled.")
        else:
            print(msg)

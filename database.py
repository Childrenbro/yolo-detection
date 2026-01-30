# database.py
import sqlite3
import hashlib
import os
from datetime import datetime

DB_FILE = "yolo11sxswApp.db"

def get_db_connection():
    """建立并返回数据库连接"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """
    检查并创建所有需要的数据库表。
    此函数是幂等的，可以安全地多次运行。
    """
    print("正在初始化数据库...")
    conn = get_db_connection()
    cursor = conn.cursor()

    print("检查并创建 users 表...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)

    print("检查并创建 detection_history 表...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            detection_type TEXT NOT NULL,
            source_path TEXT NOT NULL,
            detection_time TEXT NOT NULL,
            result_summary TEXT
        );
    """)
    
    # ---【新增部分】---
    print("检查并创建 feedback 表...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feedback_type TEXT NOT NULL,
            content TEXT NOT NULL,
            contact_info TEXT,
            submission_time TEXT NOT NULL
        );
    """)
    # -------------------

    conn.commit()
    conn.close()
    print("数据库表初始化完成。")


def hash_password(password):
    """对密码进行哈希处理"""
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    """添加新用户，对密码进行哈希存储"""
    if not username or not password:
        return False, "用户名或密码不能为空"
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                       (username, hash_password(password)))
        conn.commit()
        return True, "注册成功"
    except sqlite3.IntegrityError:
        return False, "用户名已存在"
    finally:
        conn.close()

def check_user(username, password):
    """验证用户名和密码"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and user['password_hash'] == hash_password(password):
        return True
    return False

def update_password(username, new_password):
    """根据用户名更新密码"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return False, "该用户名不存在"
    try:
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                       (hash_password(new_password), username))
        conn.commit()
        conn.close()
        return True, "密码重置成功！"
    except sqlite3.Error as e:
        conn.close()
        return False, f"数据库更新失败: {e}"

def add_history_record(detection_type, source_path, result_summary=""):
    """向历史记录表中添加一条新记录, 并返回该记录的ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last_id = None
    try:
        cursor.execute("""
            INSERT INTO detection_history (detection_type, source_path, detection_time, result_summary)
            VALUES (?, ?, ?, ?)
        """, (detection_type, source_path, current_time, result_summary))
        conn.commit()
        last_id = cursor.lastrowid
    except sqlite3.Error as e:
        print(f"添加历史记录失败: {e}")
    finally:
        conn.close()
    return last_id

def update_history_summary(record_id, summary):
    """根据记录ID更新结果摘要"""
    if not record_id:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE detection_history SET result_summary = ? WHERE id = ?", (summary, record_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"更新历史记录失败: {e}")
    finally:
        conn.close()

def get_all_history():
    """从历史记录表中获取所有记录，按时间倒序排列"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM detection_history ORDER BY detection_time DESC")
        records = cursor.fetchall()
        return records
    except sqlite3.Error as e:
        print(f"查询历史记录失败: {e}")
        return []
    finally:
        conn.close()

# ---【新增函数】---
def add_feedback(feedback_type, content, contact_info=""):
    """向反馈表中添加一条新记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("""
            INSERT INTO feedback (feedback_type, content, contact_info, submission_time)
            VALUES (?, ?, ?, ?)
        """, (feedback_type, content, contact_info, current_time))
        conn.commit()
        return True # 返回成功标志
    except sqlite3.Error as e:
        print(f"添加反馈失败: {e}")
        return False # 返回失败标志
    finally:
        conn.close()
# --------------------

create_tables()
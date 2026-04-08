"""
数据库迁移脚本：删除 rules 表中的 cookie_config 列

用法：
    python -m migrations.remove_cookie_config
"""
import sqlite3
import os

def migrate(db_path: str):
    """执行迁移"""
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(rules)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"当前列: {columns}")

    if "cookie_config" not in columns:
        print("cookie_config 列不存在，无需迁移")
        return True

    cursor.execute("ALTER TABLE rules DROP COLUMN cookie_config")
    print("成功删除 cookie_config 列")

    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "app.db")
    migrate(db_path)
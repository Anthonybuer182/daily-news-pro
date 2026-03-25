"""
数据库迁移脚本：为 rules 表添加 translation_config 字段

用法：
    python -m migrations.add_translation_config
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

    if "translation_config" in columns:
        print("translation_config 列已存在，跳过")
    else:
        cursor.execute("ALTER TABLE rules ADD COLUMN translation_config TEXT")
        print("成功添加 translation_config 列")

    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
    db_path = os.path.abspath(db_path)

    print(f"迁移数据库: {db_path}")
    migrate(db_path)

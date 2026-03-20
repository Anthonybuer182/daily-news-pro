"""
数据库迁移脚本：为 rules 表添加 fetch_method 字段

用法：
    python -m migrations.add_fetch_method
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

    # 检查列是否已存在
    cursor.execute("PRAGMA table_info(rules)")
    columns = [col[1] for col in cursor.fetchall()]

    if "fetch_method" in columns:
        print("fetch_method 列已存在，跳过迁移")
        return True

    # 添加新列
    try:
        cursor.execute("ALTER TABLE rules ADD COLUMN fetch_method VARCHAR(20)")
        conn.commit()
        print("成功添加 fetch_method 列")
        return True
    except sqlite3.Error as e:
        print(f"迁移失败: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # 默认数据库路径
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
    db_path = os.path.abspath(db_path)

    print(f"迁移数据库: {db_path}")
    migrate(db_path)
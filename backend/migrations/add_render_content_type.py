"""
数据库迁移脚本：为 rules 表添加 render 和 content_type 字段

用法：
    python -m migrations.add_render_content_type
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

    if "render" in columns:
        print("render 列已存在，跳过")
    else:
        cursor.execute("ALTER TABLE rules ADD COLUMN render VARCHAR(20)")
        print("成功添加 render 列")

    if "content_type" in columns:
        print("content_type 列已存在，跳过")
    else:
        cursor.execute("ALTER TABLE rules ADD COLUMN content_type VARCHAR(20)")
        print("成功添加 content_type 列")

    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    # 默认数据库路径
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
    db_path = os.path.abspath(db_path)

    print(f"迁移数据库: {db_path}")
    migrate(db_path)
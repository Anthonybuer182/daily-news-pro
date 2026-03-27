"""
数据库迁移脚本：创建 tags 表

用法：
    python -m migrations.add_tags
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

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tags'")
    if cursor.fetchone():
        print("tags 表已存在，跳过")
        conn.close()
        return True

    cursor.execute("""
        CREATE TABLE tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("成功创建 tags 表")

    # 同时为 model_configs 添加 max_tags 字段（如果不存在）
    cursor.execute("PRAGMA table_info(model_configs)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'max_tags' not in columns:
        cursor.execute("ALTER TABLE model_configs ADD COLUMN max_tags INTEGER DEFAULT 3")
        print("成功为 model_configs 添加 max_tags 字段")
    else:
        print("model_configs.max_tags 字段已存在，跳过")

    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
    db_path = os.path.abspath(db_path)

    print(f"迁移数据库: {db_path}")
    migrate(db_path)

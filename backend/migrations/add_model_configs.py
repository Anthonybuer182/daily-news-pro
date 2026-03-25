"""
数据库迁移脚本：创建 model_configs 表

用法：
    python -m migrations.add_model_configs
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

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='model_configs'")
    if cursor.fetchone():
        print("model_configs 表已存在，跳过")
        conn.close()
        return True

    cursor.execute("""
        CREATE TABLE model_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            api_base VARCHAR(500) NOT NULL,
            api_key VARCHAR(500) NOT NULL,
            model VARCHAR(100) NOT NULL,
            is_default BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("成功创建 model_configs 表")

    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
    db_path = os.path.abspath(db_path)

    print(f"迁移数据库: {db_path}")
    migrate(db_path)
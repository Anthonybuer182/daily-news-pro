"""
数据库迁移脚本：为 rules 表添加缺失字段

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

    cursor.execute("PRAGMA table_info(rules)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"当前列: {columns}")

    columns_to_add = {
        "render": "VARCHAR(20)",
        "content_type": "VARCHAR(20)",
        "source_url": "VARCHAR(500)",
        "field_mapping": "TEXT",
        "extract_config": "TEXT",
        "request_config": "TEXT",
        "list_selector_type": "VARCHAR(50) DEFAULT 'css'",
        "list_selector": "VARCHAR(1000)",
        "list_item_selector": "VARCHAR(1000)",
        "detail_url_pattern": "VARCHAR(1000)",
        "title_selector_type": "VARCHAR(50) DEFAULT 'css'",
        "title_selector": "VARCHAR(1000)",
        "content_selector_type": "VARCHAR(50) DEFAULT 'css'",
        "content_selector": "VARCHAR(1000)",
        "author_selector_type": "VARCHAR(50) DEFAULT 'css'",
        "author_selector": "VARCHAR(1000)",
        "publish_time_selector_type": "VARCHAR(50) DEFAULT 'css'",
        "publish_time_selector": "VARCHAR(1000)",
        "cover_image_selector": "VARCHAR(1000)",
        "exclude_patterns": "TEXT",
        "cookie_config": "TEXT",
        "headers_config": "TEXT",
        "auth_type": "VARCHAR(50) DEFAULT 'none'",
        "auth_config": "TEXT",
        "proxy_config": "VARCHAR(500)",
        "delay_min": "INTEGER DEFAULT 1",
        "delay_max": "INTEGER DEFAULT 3",
        "user_agent": "VARCHAR(500)",
        "cron_expression": "VARCHAR(100)",
    }

    for col_name, col_type in columns_to_add.items():
        if col_name in columns:
            print(f"{col_name} 列已存在，跳过")
        else:
            cursor.execute(f"ALTER TABLE rules ADD COLUMN {col_name} {col_type}")
            print(f"成功添加 {col_name} 列")

    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
    db_path = os.path.abspath(db_path)

    print(f"迁移数据库: {db_path}")
    migrate(db_path)
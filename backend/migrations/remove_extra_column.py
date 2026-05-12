"""
数据库迁移脚本：移除 articles.extra 列

用法：
    python -m migrations.remove_extra_column

注意：SQLite 不支持 DROP COLUMN，需要重建表
"""
import sqlite3
import os


def migrate(db_path: str):
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(articles)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"当前列: {columns}")

    if "extra" not in columns:
        print("extra 列不存在，无需迁移")
        conn.close()
        return True

    new_columns = [col for col in columns if col != "extra"]
    print(f"保留的列: {new_columns}")

    # 用完整 DDL 重建表，保留 PRIMARY KEY / FOREIGN KEY / 索引
    cursor.execute("""
        CREATE TABLE articles_new (
            id INTEGER NOT NULL,
            rule_id INTEGER,
            url VARCHAR(1000) NOT NULL,
            title VARCHAR(500),
            summary TEXT,
            author VARCHAR(255),
            publish_time DATETIME,
            cover_image VARCHAR(500),
            markdown_file VARCHAR(500),
            status VARCHAR(20) DEFAULT 'pending',
            error_message TEXT,
            tags TEXT,
            images TEXT,
            created_at DATETIME,
            updated_at DATETIME,
            PRIMARY KEY (id),
            FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE
        )
    """)
    cursor.execute(f"""
        INSERT INTO articles_new
        SELECT {', '.join(new_columns)}
        FROM articles
    """)
    cursor.execute("DROP TABLE articles")
    cursor.execute("ALTER TABLE articles_new RENAME TO articles")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_articles_id ON articles (id)")

    cursor.execute("PRAGMA table_info(articles)")
    final_columns = [col[1] for col in cursor.fetchall()]
    print(f"迁移后列: {final_columns}")

    conn.commit()
    conn.close()
    print("extra 列已移除")
    return True


if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
    db_path = os.path.abspath(db_path)

    print(f"迁移数据库: {db_path}")
    migrate(db_path)

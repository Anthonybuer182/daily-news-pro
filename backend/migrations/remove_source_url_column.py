"""
数据库迁移脚本：移除 source_url 列

用法：
    python -m migrations.remove_source_url_column

注意：SQLite 不支持 DROP COLUMN，需要重建表
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

    if "source_url" not in columns:
        print("source_url 列不存在，无需迁移")
        conn.close()
        return True

    cursor.execute("SELECT * FROM rules LIMIT 1")
    all_columns = [description[0] for description in cursor.description]
    print(f"所有列: {all_columns}")

    new_columns = [col for col in all_columns if col != "source_url"]
    print(f"保留的列: {new_columns}")

    temp_table = "rules_temp"
    cursor.execute(f"""
        CREATE TABLE {temp_table} AS
        SELECT {', '.join(new_columns)}
        FROM rules
    """)

    cursor.execute("DROP TABLE rules")
    cursor.execute(f"ALTER TABLE {temp_table} RENAME TO rules")

    cursor.execute("PRAGMA table_info(rules)")
    final_columns = [col[1] for col in cursor.fetchall()]
    print(f"迁移后列: {final_columns}")

    conn.commit()
    conn.close()
    print("source_url 列已移除")
    return True


if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")
    db_path = os.path.abspath(db_path)

    print(f"迁移数据库: {db_path}")
    migrate(db_path)
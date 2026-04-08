"""
迁移脚本：将 detail_url_pattern 和 exclude_patterns 迁移到 extract_config.list.url_filters

此脚本用于将旧的独立字段迁移到新的内嵌结构。

使用方法：
    python migrations/migrate_url_filters_to_extract_config.py

迁移逻辑：
1. 读取每条 Rule
2. 如果 detail_url_pattern 或 exclude_patterns 有值
3. 解析 extract_config JSON
4. 在 list 下添加 url_filters 配置
5. 保存回 extract_config
6. 可选：清空旧的 detail_url_pattern 和 exclude_patterns 字段（注释掉，默认不执行）
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.rule import Rule


def migrate_url_filters():
    db = SessionLocal()
    try:
        rules = db.query(Rule).all()
        migrated_count = 0

        for rule in rules:
            changed = False
            extract_config = {}

            if rule.extract_config:
                try:
                    extract_config = json.loads(rule.extract_config)
                except json.JSONDecodeError:
                    print(f"Rule {rule.id} ({rule.name}): extract_config JSON 解析失败，跳过")
                    continue

            list_config = extract_config.get("list", {})

            if rule.detail_url_pattern or rule.exclude_patterns:
                if "url_filters" not in list_config:
                    url_filters = {}

                    if rule.detail_url_pattern:
                        url_filters["include"] = rule.detail_url_pattern

                    if rule.exclude_patterns:
                        try:
                            exclude = json.loads(rule.exclude_patterns)
                            if isinstance(exclude, list):
                                url_filters["exclude"] = exclude
                            else:
                                url_filters["exclude"] = [exclude]
                        except json.JSONDecodeError:
                            url_filters["exclude"] = [rule.exclude_patterns]

                    list_config["url_filters"] = url_filters
                    extract_config["list"] = list_config
                    rule.extract_config = json.dumps(extract_config, ensure_ascii=False)

                    migrated_count += 1
                    print(f"Rule {rule.id} ({rule.name}): 已迁移")
                    print(f"  - include: {url_filters.get('include')}")
                    print(f"  - exclude: {url_filters.get('exclude')}")

                    changed = True

            if changed:
                db.commit()

        print(f"\n迁移完成，共迁移 {migrated_count} 条规则")

    except Exception as e:
        print(f"迁移失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("开始迁移 url_filters 配置到 extract_config...")
    migrate_url_filters()
    print("迁移完成！")

"""
修复技能描述 - 从 SKILL.md 文件中提取正确描述
"""
import asyncio
import sqlite3
from pathlib import Path
import sys
sys.path.insert(0, '.')

# 解析 SKILL.md 文件提取描述
def extract_description_from_md(skill_dir: Path) -> str:
    """从 SKILL.md 或 skill.md 提取描述"""
    skill_md = skill_dir / "skill.md"
    if not skill_md.exists():
        skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        return f"{skill_dir.name} - 技能"

    content = skill_md.read_text(encoding="utf-8", errors="ignore")
    lines = content.split("\n")

    # 跳过 YAML front matter
    start_index = 0
    if lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                start_index = i + 1
                break

    # 查找描述
    description = ""
    for line in lines[start_index:start_index + 30]:
        line = line.strip()
        if line.startswith("#"):
            description = line.lstrip("#").strip()
            break
        if line and not line.startswith("<!--") and not line.startswith("---") and not line.startswith("==="):
            description = line[:200]
            break

    if not description or len(description) < 5:
        description = f"{skill_dir.name} - 技能"

    return description

# 主函数
def main():
    db_path = "aigc.db"
    if not Path(db_path).exists():
        print(f"数据库文件不存在: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有技能
    cursor.execute("SELECT id, name, skill_path FROM skills WHERE status = 'testing'")
    skills = cursor.fetchall()

    count = 0
    for skill_id, name, skill_path in skills:
        skill_dir = Path(skill_path)
        if not skill_dir.exists():
            continue

        # 提取新描述
        new_description = extract_description_from_md(skill_dir)

        # 获取旧描述
        cursor.execute("SELECT description FROM skills WHERE id = ?", (skill_id,))
        old_description = cursor.fetchone()[0]

        # 更新描述
        if old_description != new_description:
            cursor.execute("UPDATE skills SET description = ? WHERE id = ?", (new_description, skill_id))
            count += 1
            print(f"✓ {name}: {new_description[:50]}...")

    conn.commit()
    conn.close()

    print(f"\n✓ 已修复 {count} 个技能的描述")

if __name__ == "__main__":
    main()

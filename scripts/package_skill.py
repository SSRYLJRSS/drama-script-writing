#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI短剧剧本 skill 打包脚本
==================================
用法：
    python package_skill.py               # 交互式询问打包模式
    python package_skill.py --clean       # 干净版：learnings.md 重置为空白模板
    python package_skill.py --experience  # 带经验版：保留 learnings.md 全部内容

两种模式都会：
    1. 检查敏感痕迹（违规自动剔除或警告）
    2. 输出 zip 到 skill 上级目录
    3. 打印包内容清单和校验结果

无第三方依赖（只用 Python 标准库），Windows/Mac/Linux 均可运行。
"""

import os
import sys
import shutil
import zipfile
import argparse
from datetime import datetime

# ---------------------------------------------------------------
# 常量
# ---------------------------------------------------------------
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIR = os.path.join(SKILL_DIR, "scripts")
LEARNINGS_FILE = os.path.join(SKILL_DIR, "learnings.md")
LEARNINGS_TEMPLATE = os.path.join(SCRIPT_DIR, "learnings_template.md")
DEFAULT_ZIP_NAME = "AI短剧剧本撰写"
ARC_ROOT = "drama-script-writing"

# 需要清理的敏感痕迹（普通字符串匹配）
FORBIDDEN_PATTERNS = [
    "爱德华",
    "F:\\", "F:/",
    "C:\\Users\\",
    "ZHIHU_ACCESS",
    "agent-reach-venv",
    ".hermes/shared-skills",
    "老板",
    "edward-copywriting",
    "finance-video-copywriting",
]

# 打包时排除的文件/目录
EXCLUDE = {
    "__pycache__", ".git", ".DS_Store", "Thumbs.db",
}


# ---------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------
def banner(msg):
    print("\n" + "=" * 60)
    print(f"  {msg}")
    print("=" * 60)


def check_forbidden(content, filename):
    violations = []
    for pat in FORBIDDEN_PATTERNS:
        if pat in content:
            count = content.count(pat)
            violations.append(f"{pat} (x{count})")
    return violations


def scan_skill():
    results = []
    for root, dirs, files in os.walk(SKILL_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE]
        for f in files:
            if f in EXCLUDE or f == "package_skill.py":
                continue
            fpath = os.path.join(root, f)
            rel = os.path.relpath(fpath, SKILL_DIR)
            is_violation = False
            if f.endswith((".md", ".txt", ".py", ".json", ".yaml", ".yml")):
                try:
                    with open(fpath, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    if check_forbidden(content, rel):
                        is_violation = True
                except Exception:
                    pass
            results.append((rel, is_violation))
    return results


def reset_learnings():
    if os.path.exists(LEARNINGS_TEMPLATE):
        shutil.copy2(LEARNINGS_TEMPLATE, LEARNINGS_FILE)
        print("  ✅ learnings.md 已重置为空白模板")
    else:
        print("  ⚠️ 未找到模板文件，保留当前 learnings.md")


def make_zip():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parent = os.path.dirname(SKILL_DIR)
    zip_name = f"{DEFAULT_ZIP_NAME}_{timestamp}"
    zip_path = os.path.join(parent, zip_name + ".zip")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(SKILL_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE]
            for f in files:
                if f in EXCLUDE:
                    continue
                fpath = os.path.join(root, f)
                arcname = os.path.join(
                    ARC_ROOT,
                    os.path.relpath(fpath, SKILL_DIR)
                )
                zf.write(fpath, arcname)

    return zip_path


def verify_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        print(f"  文件数: {len(zf.namelist())}")
        print(f"  大小: {os.path.getsize(zip_path) / 1024:.1f}KB")
        print("  内容:")
        for name in sorted(zf.namelist()):
            print(f"    {name}")
        ok = True
        for name in zf.namelist():
            if name.endswith((".md", ".txt")):
                content = zf.read(name).decode("utf-8")
                violations = check_forbidden(content, name)
                if violations:
                    print(f"  ❌ {name}: {violations}")
                    ok = False
        if ok:
            print("  ✅ 敏感痕迹检查通过")
        return ok


# ---------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="打包 AI短剧剧本撰写 skill")
    parser.add_argument("--clean", action="store_true", help="干净版：learnings重置")
    parser.add_argument("--experience", action="store_true", help="带经验版：learnings保留")
    args = parser.parse_args()

    if args.clean:
        mode = "clean"
    elif args.experience:
        mode = "experience"
    else:
        print("\n请选择打包模式：")
        print("  1. 干净版（learnings重置为空白模板，适合分享给别人）")
        print("  2. 带经验版（保留learnings全部内容，适合团队内部）")
        choice = input("\n输入 1 或 2: ").strip()
        mode = "clean" if choice == "1" else "experience"

    banner(f"打包模式：{'干净版' if mode == 'clean' else '带经验版'}")

    # 敏感痕迹扫描
    banner("敏感痕迹扫描")
    files = scan_skill()
    violations_found = False
    for rel, is_violation in files:
        if is_violation:
            print(f"  ❌ {rel}: 敏感痕迹")
            violations_found = True
    if not violations_found:
        print("  ✅ 所有文件干净")

    # learnings.md 处理
    banner("learnings.md 处理")
    if mode == "clean":
        reset_learnings()
    else:
        learnings_size = os.path.getsize(LEARNINGS_FILE) / 1024
        print(f"  ✅ 保留当前 learnings.md（{learnings_size:.1f}KB）")

    # 打包
    banner("打包")
    zip_path = make_zip()

    # 校验
    banner("校验")
    ok = verify_zip(zip_path)

    banner("完成")
    print(f"\n  📦 zip 文件：{zip_path}")
    print(f"  📄 解压后把 drama-script-writing 文件夹放入目标环境的 skills 目录即可使用。")
    if mode == "clean":
        print("  ℹ️ 注意：此包为干净版，learnings.md 已重置。")
    else:
        print("  ℹ️ 注意：此包带个人经验，分享前请确认内容适合公开。")

    if not ok:
        print("  ⚠️ 警告：包内发现敏感痕迹，请检查后再分享！")
        sys.exit(1)


if __name__ == "__main__":
    main()
